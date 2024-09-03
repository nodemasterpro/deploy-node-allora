# Allora Node Deployment
This repository contains Ansible scripts for the installation, updating, and removal of Allora validator nodes on Linux systems. The playbooks are designed to simplify the process of setting up Allora nodes, managing their services, and ensuring seamless node operations.

## Prerequisites
Recommended specifications for a server:

System: Linux Ubuntu 22.04 with docker installed.
Memory: 16 GB
CPU: 6 cores
Disk: 1 TB SSD
Open TCP ports: 26656, 26657 must be open and accessible.
For hosting Allora nodes, opt for a VPS 2 server from Contabo.

## Getting Started
## Step 1: Installing Dependencies
Update your system's package list and install necessary tools:


```
sudo apt update && sudo apt upgrade -y
```
```
sudo apt install ansible git -y
```
## Step 2: Downloading the Project
Clone this repository to access the Ansible playbook and all necessary files:


```
git clone https://github.com/nodemasterpro/deploy-node-allora.git
cd deploy-node-allora
```

## Step 3: Installing Allora Validator Node
Execute the playbook using the following command, specifying the 'moniker' (node name) as an extra variable:

```
ansible-playbook install_validator_node_allora.yml -e moniker="your_node_name"
```
Note: Replace "your_node_name" with the unique name you wish to assign to your node.

## Step 4: Viewing Node Logs
To view the logs for the Allora validator node:

```
journalctl -u allora-node -f -o cat
```

## Step 5: Creating a Wallet
After installing the node, create a wallet essential for network operations:

```
ansible-playbook create_wallet_allora.yml -e wallet_name="your_wallet_name"
```
Once completed, You can find the wallet information, including private key, seed phrase, and hexadecimal address, in "/root/.allorad/wallets/<your_wallet_name>.info". Save it, as it will be useful for the following steps.

## Step 6: Requesting Allora Testnet Funds
Get funds for your wallet via the Allora faucet. Enter the address of your wallet, verify that you are human, and request testnet tokens.

## Step 7: Node Synchronization Verification
Ensure your node is fully synchronized with the Allora blockchain:

```
allorad status | jq .result.sync_info
```
Wait until the catching_up variable is false. Synchronization time may vary.

## Step 8: Creating the Validator and Linking it with the Wallet
To finalize the setup of your node, create a validator:

```
ansible-playbook register_validator_node_allora.yml
```
During this process, you will be prompted to enter two values:

wallet_name: The name of your wallet.
moniker: The name of your node.
Once completed, you will obtain the address of your validator node.

Check the status of your node:

```
allorad q staking validator <validator_address>
```

##Step 9: Installing the Allora Worker Node
Once the project files are ready, initiate the installation of the Allora worker node using this command:

```
ansible-playbook install_worker_node_allora.yml
```

Step 10: Viewing Worker Node Logs
To display all the logs, type this command:

```
journalctl -u allora-worker-node -f -o cat
```
To display only the node worker logs, type this command:

```
docker logs -f worker-basic-eth-pred
```
To exit the logs, type Ctrl+C.

Step 11: Checking the Worker Node
To check that your worker node is functioning correctly, run this command:

```
curl -X POST 'http://localhost:6000/api/v1/functions/execute' \
-H 'Content-Type: application/json' \
-d '{
 "function_id": "bafybeigpiwl3o73zvvl6dxdqu7zqcub5mhg65jiky2xqb4rdhfmikswzqm",
 "method": "allora-inference-function.wasm",
 "parameters": null,
 "topic": "1",
 "config": {
 "env_vars": [
 {
 "name": "BLS_REQUEST_PATH",
 "value": "/api"
 },
 {
 "name": "ALLORA_ARG_PARAMS",
 "value": "ETH"
 }
 ],
 "number_of_nodes": -1,
 "timeout": 2
 }
}'
```
You should get this type of response:

```
{"code":"200","request_id":"565ce0b0-3847-45fb-975d-4812f3d14707","results":[{"result":{"stdout":"{\"infererValue\": \"2917.167872527247\"}\n\n","stderr":"","exit_code":0},"peers":["12D3KooWEEBpBSez1q8jLFTd2m5mUfeY3yg7gQsTkecPoZAMXPQZ"],"frequency":100}],"cluster":{"peers":["12D3KooWEEBpBSez1q8jLFTd2m5mUfeY3yg7gQsTkecPoZAMXPQZ"]}
```
Code 200 means the answer is correct. Congratulations! Your Allora worker node is operational.


## Additional Information
Stopping Service
To stop the Allora validator node:

```
systemctl stop allora-node
```

To stop the Allora worker node:
```
systemctl stop allora-worker-node

```
Starting Service
To start the Allora validator node:

```
systemctl start allora-node
```
```
systemctl start allora-worker-node
```

Removing the Allora Validator Node
To remove the Allora validator node, run this playbook:

```
ansible-playbook remove_worker_node_allora.yml
```

To remove the Allora worker node, run this playbook:

```
ansible-playbook remove_worker_node_allora.yml
```

Ensure to back up all important data before deleting the Allora node, as this action may remove node data.

By following this guide, you have successfully deployed and managed Allora validator nodes, contributing to the robustness of the network and potentially earning rewards. Join the Allora community on Discord and Twitter to stay informed about the project.

Thank you for taking the time to read this guide! If you have any questions or would like to continue the conversation, feel free to join the Allora Discord server. Stay updated and connected: Follow us on Twitter, join our Telegram group, Discord server, and subscribe to our YouTube channel.






