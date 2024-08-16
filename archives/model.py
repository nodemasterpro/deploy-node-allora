import os
import time
import requests
import numpy as np
import pandas as pd
from requests.exceptions import RequestException
from transformers import TimeSeriesTransformerForPrediction, TimeSeriesTransformerConfig
from transformers import Trainer, TrainingArguments
import torch
import logging
import sys
from datetime import datetime, timedelta
import zipfile

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info(f"Python version: {sys.version}")
logger.info(f"Python path: {sys.path}")

try:
    import binance
    logger.info(f"Binance version: {binance.__version__}")
    from binance.client import Client as Spot
    logger.info("Successfully imported Binance Client")
except ImportError as e:
    logger.error(f"Error importing binance: {e}")
    Spot = None

# Configuration
INFERENCE_API_ADDRESS = os.getenv('INFERENCE_API_ADDRESS', 'http://inference:8000')
TOPIC_ID = os.getenv('TOPIC_ID', '1')
binance_data_path = "/app/data/binance"
training_price_data_path = "/app/data/training_price_data.csv"
model_file_path = "/app/model/price_prediction_model.pt"


def get_token_from_topic_id(topic_id):
    topic_id_to_token = {
        '1': 'ETH',
        '3': 'BTC',
        '5': 'SOL'
    }
    return topic_id_to_token.get(topic_id, 'ETH')

# Création des répertoires nécessaires
os.makedirs(os.path.dirname(binance_data_path), exist_ok=True)
os.makedirs(os.path.dirname(training_price_data_path), exist_ok=True)
os.makedirs(os.path.dirname(model_file_path), exist_ok=True)

def download_binance_monthly_data(cm_or_um, symbols, intervals, years, months, download_path):
    for symbol in symbols:
        for interval in intervals:
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
                    except RequestException as e:
                        logger.error(f"Failed to download {file_name}: {e}")

def download_binance_daily_data(cm_or_um, symbols, intervals, year, month, download_path):
    for symbol in symbols:
        for interval in intervals:
            file_name = f"{symbol}-{interval}-{year}-{month:02d}.zip"
            url = f"https://data.binance.vision/data/spot/daily/klines//{symbol}/{interval}/{file_name}"
            file_path = os.path.join(download_path, file_name)
            
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Successfully downloaded {file_name}")
                
            except RequestException as e:
                logger.error(f"Failed to download {file_name}: {e}")
            
            except IOError as e:
                logger.error(f"Failed to write file {file_name}: {e}")
            
            except Exception as e:
                logger.error(f"Unexpected error while downloading {file_name}: {e}")

    logger.info(f"Finished downloading daily data for {year}-{month:02d}")
    
def download_data():
    cm_or_um = "um"
    symbols = ["ETHUSDT"]
    intervals = ["1d"]
    years = ["2020", "2021", "2022", "2023", "2024"]
    months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    os.makedirs(binance_data_path, exist_ok=True)
    download_binance_monthly_data(cm_or_um, symbols, intervals, years, months, binance_data_path)
    logger.info(f"Downloaded monthly data to {binance_data_path}.")
    current_datetime = datetime.now()
    current_year = current_datetime.year
    current_month = current_datetime.month
    download_binance_daily_data(cm_or_um, symbols, intervals, current_year, current_month, binance_data_path)
    logger.info(f"Downloaded daily data to {binance_data_path}.")

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
                    df = df.iloc[:, :11]
                    df.columns = ["start_time", "open", "high", "low", "close", "volume", "end_time", "volume_usd", "n_trades", "taker_volume", "taker_volume_usd"]
                    df["end_time"] = pd.to_datetime(df["end_time"], unit="ms")
                    df.set_index("end_time", inplace=True)
                    price_df = pd.concat([price_df, df])
                logger.info(f"Processed {file}")
            except Exception as e:
                logger.error(f"Error processing {file}: {e}")

    if price_df.empty:
        logger.warning("No data processed. price_df is empty.")
        return False

    price_df.sort_index(inplace=True)
    price_df.to_csv(training_price_data_path)
    logger.info(f"Formatted data saved to {training_price_data_path}")
    return True

def train_model():
    price_data = pd.read_csv(training_price_data_path)
    df = pd.DataFrame()

    df["date"] = pd.to_datetime(price_data["end_time"])
    df["date"] = df["date"].map(pd.Timestamp.timestamp)

    df["price"] = price_data[["open", "close", "high", "low"]].mean(axis=1)

    x = df["date"].values.reshape(-1, 1)
    y = df["price"].values.reshape(-1, 1)

    # Initialisation du modèle
    config = TimeSeriesTransformerConfig(
        prediction_length=10,
        context_length=60,
        num_time_features=1,
        num_static_categorical_features=0,
        num_static_real_features=0,
    )
    model = TimeSeriesTransformerForPrediction(config)

    # Préparation des données pour l'entraînement
    train_dataset = []
    for i in range(len(x) - config.context_length - config.prediction_length + 1):
        past_values = torch.tensor(y[i:i+config.context_length].flatten(), dtype=torch.float32).unsqueeze(0)
        future_values = torch.tensor(y[i+config.context_length:i+config.context_length+config.prediction_length].flatten(), dtype=torch.float32).unsqueeze(0)
        past_time_features = torch.tensor(x[i:i+config.context_length].flatten(), dtype=torch.float32).unsqueeze(0)
        future_time_features = torch.tensor(x[i+config.context_length:i+config.context_length+config.prediction_length].flatten(), dtype=torch.float32).unsqueeze(0)
        
        train_dataset.append({
            "past_values": past_values,
            "past_time_features": past_time_features,
            "past_observed_mask": torch.ones_like(past_values, dtype=torch.bool),
            "future_values": future_values,
            "future_time_features": future_time_features,
            "future_observed_mask": torch.ones_like(future_values, dtype=torch.bool),
        })

    # Entraînement du modèle
    training_args = TrainingArguments(
        output_dir="./results",
        num_train_epochs=3,
        per_device_train_batch_size=32,
        logging_dir="./logs",
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
    )
    trainer.train()

    # Sauvegarde du modèle
    torch.save(model.state_dict(), model_file_path)
    logger.info(f"Trained TimeSeriesTransformer model saved to {model_file_path}")
    
def make_prediction(model):
    current_timestamp = datetime.now().timestamp()
    next_timestamp = current_timestamp + 600  # Ajoute 10 minutes en secondes
    logger.info(f"Prédiction pour le timestamp : {next_timestamp}")
    
    try:
        prediction = model.predict([[next_timestamp]])
        logger.info(f"Prédiction brute : {prediction}, type : {type(prediction)}")
        
        if isinstance(prediction, np.ndarray):
            prediction = prediction.item() if prediction.size == 1 else prediction[0]
        elif isinstance(prediction, list):
            prediction = prediction[0]
        
        logger.info(f"Prédiction traitée : {prediction}, type : {type(prediction)}")
        return float(prediction)
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction : {e}")
        return None

def main():
    logger.info("Démarrage de la fonction principale")
    
    # Vérifiez si le modèle existe, sinon entraînez et sauvegardez le modèle
    if not os.path.exists(model_file_path):
        logger.info(f"Fichier de modèle non trouvé à {model_file_path}. Entraînement du modèle.")
        download_data()
        if format_data():
            train_model()
        else:
            logger.error("Échec du formatage des données. Sortie du programme.")
            return

    # Chargement du modèle
    try:
        config = TimeSeriesTransformerConfig(
            prediction_length=10,  # Prédire les 10 prochaines minutes
            context_length=60,  # Utiliser les 60 dernières minutes pour la prédiction
            num_time_features=1,
            num_static_categorical_features=0,
            num_static_real_features=0,
        )
        model = TimeSeriesTransformerForPrediction(config)
        model.load_state_dict(torch.load(model_file_path))
        logger.info(f"Modèle chargé avec succès. Type : {type(model)}")
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle : {e}")
        return

    while True:
        try:
            logger.info("Début d'un nouveau cycle")
            
            # Étape 1 : Récupération des données
            logger.info("Récupération des données de l'API d'inférence")
            current_price = get_data_from_inference_api()
            logger.info(f"Données récupérées : {current_price}")
            
            if current_price is None:
                logger.warning("Aucune donnée reçue, cycle ignoré")
                time.sleep(10)
                continue
            
            # Définir le token ici
            token = get_token_from_topic_id(TOPIC_ID)
            
            # Étape 2 : Préparation des données pour la prédiction
            logger.info("Préparation des données pour la prédiction")
            current_timestamp = datetime.now().timestamp()
            next_timestamp = current_timestamp + 600  # Ajoute 10 minutes en secondes
            
            # Étape 3 : Prédiction
            logger.info("Réalisation de la prédiction")
            prediction = make_prediction(model)
            if prediction is None:
                logger.warning("Échec de la prédiction, cycle ignoré")
                time.sleep(10)
                continue
               
            # Étape 4 : Journalisation de la prédiction
            logger.info(f"Prédiction pour {token}: {prediction}")

        except Exception as e:
            logger.error(f"Erreur dans la boucle principale : {e}")
            logger.exception("Détails de l'exception :")
        
        # Ajout d'une pause de 10 secondes à la fin de chaque cycle
        time.sleep(5)

if __name__ == "__main__":
    main()