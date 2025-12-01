#!/bin/bash
# Script to create and enable 4GB of swap memory
# Run this on your Oracle Cloud VM instance (host machine)

echo "Checking for existing swap..."
sudo swapon --show

if [ $(sudo swapon --show | wc -l) -eq 0 ]; then
    echo "No swap found. Creating 4GB swap file..."
    
    # Create a 4GB file
    sudo fallocate -l 4G /swapfile
    
    # Secure the file
    sudo chmod 600 /swapfile
    
    # Mark as swap
    sudo mkswap /swapfile
    
    # Enable swap
    sudo swapon /swapfile
    
    # Persist in /etc/fstab
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    
    echo "Swap created successfully!"
    
    # Adjust swappiness (optional, encourages using swap)
    sudo sysctl vm.swappiness=10
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
else
    echo "Swap already exists."
fi

free -h
