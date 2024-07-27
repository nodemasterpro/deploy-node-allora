#!/bin/bash

# Check if an argument is provided
if [ -z "$1" ]; then
  # Prompt for topic input if no argument is provided
  read -p "Enter topic (default: allora-topic-1-worker): " TOPIC
  TOPIC=${TOPIC:-allora-topic-1-worker}
else
  # Use the provided argument as the topic
  TOPIC=$1
fi

# Parse TOPIC_ID
TOPIC_ID=$(echo "$TOPIC" | awk -F'-' '{print $NF}')
echo "Parsed TOPIC_ID: $TOPIC_ID"

# Determine the token based on TOPIC_ID
case "$TOPIC_ID" in
  1) TOKEN="ETH" ;;
  2) TOKEN="ETH" ;;
  3) TOKEN="BTC" ;;
  4) TOKEN="BTC" ;;
  5) TOKEN="SOL" ;;
  6) TOKEN="SOL" ;;
  7) TOKEN="ETH" ;;
  8) TOKEN="BNB" ;;
  9) TOKEN="ARB" ;;
  *) TOKEN="ETH" ;; # Default action set to ETH for invalid TOPIC_ID
esac

echo "Token: $TOKEN"

# Get the current block height
block_height=$(curl -s https://allora-rpc.testnet-1.testnet.allora.network/block | jq -r .result.block.header.height)

# Perform the curl request with the parsed topic and block height
response=$(curl --silent --location 'http://localhost:6000/api/v1/functions/execute' \
--header 'Content-Type: application/json' \
--data '{
    "function_id": "bafybeigpiwl3o73zvvl6dxdqu7zqcub5mhg65jiky2xqb4rdhfmikswzqm",
    "method": "allora-inference-function.wasm",
    "parameters": null,
    "topic": "'$TOPIC_ID'",
    "config": {
        "env_vars": [
            {
                "name": "BLS_REQUEST_PATH",
                "value": "/api"
            },
            {
                "name": "ALLORA_ARG_PARAMS",
                "value": "'$TOKEN'"
            },
            {
                "name": "ALLORA_BLOCK_HEIGHT_CURRENT",
                "value": "'$block_height'"
            }
        ],
        "number_of_nodes": -1,
        "timeout": 10
    }
}')

# Print the response
echo "Response:"
echo "$response" | jq .