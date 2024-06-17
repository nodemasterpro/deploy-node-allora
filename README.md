# 0G Node Deployment
This repository contains Ansible scripts for the installation, updating, and removal of 0G validator and storage nodes on Linux systems. The playbooks are designed to simplify the process of setting up 0G nodes, managing their services, and ensuring seamless node operations.

## Prerequisites
Recommended specifications for a server:

Memory: 64 GB
CPU: 8 cores
Disk: 1 TB SSD
Open TCP ports: 8545, 8546, 26657, 5678, 26656, 9090, 9091, 1234, 6060, 5679 must be open and accessible.
For hosting 0G nodes, opt for a VPS 4 server from Contabo. Follow the Contabo VPS Server Guide for easy setup.

## Getting Started
## Step 1: Installing Dependencies
Update your system's package list and install necessary tools:

```
sudo apt update && sudo apt upgrade -y
sudo apt install ansible git -y
```

## Step 2: Downloading the Project
Clone this repository to access the Ansible playbook and all necessary files:

```
git clone https://github.com/nodemasterpro/deploy-node-0G.git
cd deploy-node-0G
```

## Step 3: Installing 0G Validator Node
Execute the playbook using the following command, specifying the 'moniker' (node name) as an extra variable:

```
ansible-playbook install_validator_node_0G.yml -e moniker="your_node_name"
```
Note: Replace "your_node_name" with the unique name you wish to assign to your node.

## Step 4: Viewing Node Logs
To view the logs for the 0G validator node:

```
journalctl -u 0gd-node -f -o cat
```
## Step 5: Creating a 0G Wallet
After installing the node, create a 0G wallet essential for network operations:

```
ansible-playbook create_wallet_0G.yml
```
Once completed, you can find the wallet information, including private key, seed phrase, and hexadecimal address, in /root/0gchain/wallets/<your_wallet_name>.info.

## Step 6: Requesting 0G Testnet Funds
Get funds for your wallet via the 0G faucet. Enter the hexadecimal address of your wallet, check the box "I am a human", and click on "Request an AOGI token". Claim at least 2 AOGI for staking and gas fees.

## Step 7: Import Your Wallet to Metamask
Import your private key to Metamask:

Open Metamask.
Go to your account settings.
Select "Import Account" and paste your private key.
Connect to the 0G-Chain Testnet:

Open 0G Scan Testnet.
Connect your wallet.
Add and switch to the 0G-Chain Testnet.

## Step 8: Node Synchronization Verification
Ensure your node is fully synchronized with the 0G blockchain:

```
0gchaind status | jq
```
Wait until the catching_up variable is false. Synchronization time takes between 30 minutes to an hour.

## Step 9: Creating the Validator and Linking it with the 0G Wallet
To finalize the setup of your node, create a validator:

```
ansible-playbook register_validator_node_0G.yml
```
During this process, you will be prompted to enter two values:

wallet_name: The name of your wallet.
moniker: The name of your node.
Once completed, you will obtain the address of your validator node. You can also get it with this command:

```
0gchaind keys show <your_wallet_name> -a --bech val --keyring-backend test
```
Check the status of your node:

```
0gchaind query staking validator <validator_address>
```
To delegate tokens to your node:

```
0gchaind tx staking delegate $(0gchaind keys show <your_wallet_name> --bech val -a --keyring-backend test) 1000000ua0gi --from <your_wallet_name> --gas=auto --gas-adjustment=1.4 --keyring-backend test -y
```

## Step 10: Join 0G Discord Server and Check Validator Node Status
Join the 0G Discord server and obtain the @Node Operators, @Developer, and @Testnet Validator roles by navigating to the roles channel and clicking on the corresponding emojis to claim these roles. Then, navigate to the #node-status channel and type:

```
!val <your_validator_address>
```
Installing the 0G Storage Node
The 0G Storage Node is crucial for maintaining the data availability and storage functionality of the 0G network. To install the storage node, run the following command:

```
ansible-playbook install_storage_node_0G.yml -e wallet_name="your_wallet_name"
```
Use the same wallet name as the one used for the validator node.

Consulting the Logs
To monitor your 0G storage node's activity:

```
tail -f /root/0g-storage-node/run/log/zgs.log.*
```

## Additional Information
### Stopping Service
To stop the 0G validator node:

```
systemctl stop 0gd-node
```
To stop the 0G storage node:

```
systemctl stop zgs-node
```
### Starting Service
To start the 0G validator node:

```
systemctl start 0gd-node
```
To start the 0G storage node:

```
systemctl start zgs-node
```
Note: To start the storage node, the validator node must be started.

### Removing the 0G Validator Node and Storage Node
To remove the 0G validator node, run this playbook:

```
ansible-playbook remove_validator_node_0G.yml
```
To remove the 0G storage node, run this playbook:

```
ansible-playbook remove_storage_node_0G.yml
```
Ensure to back up all important data before deleting the 0G nodes, as this action may remove node data.

By following this guide, you have successfully deployed and managed 0G validator and storage nodes, contributing to the robustness of the network and potentially earning rewards. Join the 0G community on Discord and Twitter to stay informed about the project.

Thank you for taking the time to read this article. If you have any questions or would like to continue the conversation, feel free to join me on Discord. I invite you to take a moment to fill out this quick survey. Your feedback will help me tailor content to your needs and interests more effectively. Your voice truly matters! Feedback Pulse. Stay updated and connected: Follow me on Twitter, join my Telegram group, Discord server, and subscribe to my YouTube channel.