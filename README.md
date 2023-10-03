# Systemd Service Monitor
## Overview
This project contains scripts and configurations to monitor the status of various systemd services. When the status of a monitored service changes, an alert is sent to a predefined webhook. The code is intended to run as a systemd service under a specific service account for enhanced security.

## Requirements
Python 3.x
requests library for Python
systemd installed and running
Gchat account with the ability to create webhooks in a space

## Installation

### 1. Clone the repository
```
git clone https://github.com/irnutsmurt/SystemD-Gchat-Alert.git
cd SystemD-Gchat-Alert
```

### 2. Install Python Dependencies
```
pip install -r requirements.txt
```

### 3. Initial Service Setup
Before running the main script, populate the default services.txt file with the names of the systemd services you want to monitor. Replace the default service1, service2, service3 with a service to monitor. You can monitor as many services as you'd like.

For example:
```
nginx
redis
``` 
Upon starting of the script, it will take the services listed in the services.txt and create entries in a services.json file with the appropriate fields to greatly simplify the process of having to manually create entries.

### 4. Service Account and Systemd Service Setup
Run the systemdsetup.sh script to create a service account and register the Python script as a systemd service. This also sets appropriate permissions.

```
chmod +x systemdsetup.sh
./systemdsetup.sh
```

After running the script, you can start the service with:
```
sudo systemctl start systemdservicealert
```

### 5. Configuration
The config.ini file is where you specify parameters such as the webhook URL and the loop interval for checking service statuses. Make sure this file has chmod 600 permissions and is owned by the service account for security by using 

```
[DEFAULT]
WebhookURL=https://webhook.url/here
LoopInterval=60
```

Make sure this file has chmod 600 permissions and is owned by the service account to protect the webhook url by using

```
chown systemdservicealert config.ini && chmod 600 config.ini
```


### 6. Adding and Removing Services
To add services, list the service names line-by-line in a file named services.txt.
To remove services, list the service names line-by-line in a file named remove.txt.
On the next loop iteration, the script will automatically add or remove these services from monitoring and delete the txt files.

## Usage
Once the systemd service is started, the script will continuously monitor the defined services. Alerts will be sent to the specified webhook whenever a service status changes.

## Contributing
If you'd like to contribute, please fork the repository and use a feature branch. Pull requests are warmly welcome.

## License
This project is licensed under the MIT License - see the LICENSE.md file for details.
