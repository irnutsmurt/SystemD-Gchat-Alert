#!/bin/bash

# Create the service account if it doesn't exist
if ! id -u systemdservicealert > /dev/null 2>&1; then
    sudo useradd -r -s /bin/false systemdservicealert
fi

# Get the full path of the current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Create systemd service
echo "[Unit]
Description=Cycognito Google Chat Alert Service

[Service]
User=systemdservicealert
ExecStart=/usr/bin/python3 $DIR/monservices.py
WorkingDirectory=$DIR
Restart=always

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/systemdservicealert.service > /dev/null

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable systemdservicealert.service

echo "Done. You can now start the service with: sudo systemctl start systemdservicealert"
