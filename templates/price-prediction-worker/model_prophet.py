import os
import pandas as pd
from prophet import Prophet
import pickle
import logging
import requests
import zipfile
from datetime import datetime, timedelta
import time

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
INFERENCE_API_ADDRESS = os.getenv('INFERENCE_API_ADDRESS', 'http://inference:8000')
TOPIC_ID = os.getenv('TOPIC_ID', '1')
binance_data_path = "/app/data/binance"
training_price_data_path = "/app/data/training_price_data.csv"
model_file_path = "/app/model/price_prediction_model.pkl"

# Création des répertoires nécessaires
os.makedirs(os.path.dirname(binance_data_path), exist_ok=True)
os.makedirs(os.path.dirname(training_price_data_path), exist_ok=True)
os.makedirs(os.path.dirname(model_file_path), exist_ok=True)

def get_token_from_topic_id(topic_id):
    topic_id_to_token = {
        '1': 'ETH',
        '3': 'BTC',
        '5': 'SOL'
    }
    return topic_id_to_token.get(topic_id, 'ETH')

def download_binance_data(symbol, interval, years, months, download_path):
    for year in years:
        for month in months:
            file_name = f"{symbol}-{interval}-{year}-{month}.zip"
            url = f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/{interval}/{file_name}"
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                with open(os.path.join(download_path, file_name), "wb") as f:
                    f.write(response.content)
                logger.info(f"Downloaded {file_name}")
            except requests.RequestException as e:
                logger.error(f"Failed to download {file_name}: {e}")

def format_data():
    files = sorted(os.listdir(binance_data_path))
    if not files:
        logger.warning(f"No files found in {binance_data_path}")
        return False

    price_df = pd.DataFrame()
    for file in files:
        if file.endswith(".zip"):
            try:
                with zipfile.ZipFile(os.path.join(binance_data_path, file), "r") as zip_ref:
                    csv_file = zip_ref.namelist()[0]
                    df = pd.read_csv(zip_ref.open(csv_file))
                    df = df.iloc[:, :6]
                    df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
                    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                    price_df = pd.concat([price_df, df])
                logger.info(f"Processed {file}")
            except Exception as e:
                logger.error(f"Error processing {file}: {e}")

    if price_df.empty:
        logger.warning("No data processed. price_df is empty.")
        return False

    price_df.sort_values("timestamp", inplace=True)
    price_df.to_csv(training_price_data_path, index=False)
    logger.info(f"Formatted data saved to {training_price_data_path}")
    return True

def train_model():
    price_data = pd.read_csv(training_price_data_path)
    df = pd.DataFrame()

    df["ds"] = pd.to_datetime(price_data["timestamp"])
    df["y"] = price_data[["open", "close", "high", "low"]].mean(axis=1)

    model = Prophet(daily_seasonality=True)
    model.fit(df)

    with open(model_file_path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Trained Prophet model saved to {model_file_path}")

def load_model():
    with open(model_file_path, "rb") as f:
        model = pickle.load(f)
    return model

def make_prediction(model):
    future = model.make_future_dataframe(periods=1, freq='10min')
    forecast = model.predict(future)
    prediction = forecast.iloc[-1]['yhat']
    return float(prediction)

def get_data_from_inference_api():
    token = get_token_from_topic_id(TOPIC_ID)
    url = f"{INFERENCE_API_ADDRESS}/inference/{token}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return float(response.text)
    except requests.RequestException as e:
        logger.error(f"Failed to get data from inference API: {e}")
        return None

def main():
    if not os.path.exists(model_file_path):
        logger.info(f"Model file not found at {model_file_path}. Training the model.")
        token = get_token_from_topic_id(TOPIC_ID)
        download_binance_data(f'{token}USDT', '1h', ['2020', '2021', '2022', '2023', '2024'], 
                              ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'], 
                              binance_data_path)
        if format_data():
            train_model()
        else:
            logger.error("Failed to format data. Exiting program.")
            return

    model = load_model()

    while True:
        try:
            logger.info("Starting a new cycle")
            
            current_price = get_data_from_inference_api()
            logger.info(f"Retrieved data: {current_price}")
            
            if current_price is None:
                logger.warning("No data received, skipping cycle")
                time.sleep(10)
                continue
            
            token = get_token_from_topic_id(TOPIC_ID)
            
            prediction = make_prediction(model)
            logger.info(f"Prediction for {token}: {prediction}")

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.exception("Exception details:")
        
        time.sleep(5)

if __name__ == "__main__":
    main()