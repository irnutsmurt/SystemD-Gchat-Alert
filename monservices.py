import subprocess
import json
import logging
import configparser
import time
import requests
import re
import os
import gzip
import shutil
from os import path
from logging.handlers import TimedRotatingFileHandler

class CompressedTimedRotatingFileHandler(TimedRotatingFileHandler):
    def doRollover(self):
        super().doRollover()

        # After log rotation, compress the log file
        latest_log_file = f"{self.baseFilename}.{self.suffix}"
        with open(latest_log_file, 'rb') as f_in, gzip.open(f"{latest_log_file}.gz", 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
        os.remove(latest_log_file)

# Initialize logging
log_dir = 'log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, 'service_monitor.log')

# Base configuration
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')

# Console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logging.getLogger('').addHandler(console)

# Log rotation handler
handler = CompressedTimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=5)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logging.getLogger('').addHandler(handler)

logging.info('Script started running')

# Load configuration
logging.info('Loading configuration from config.ini')
config = configparser.ConfigParser()
config.read('config.ini')
webhook_url = config['DEFAULT']['WebhookURL']
loop_interval = int(config['DEFAULT']['LoopInterval'])

# Initialize or Update JSON file
logging.info('Checking for services.json')
existing_services = {}
if path.exists('services.json'):
    logging.info('Loading existing services from services.json')
    with open('services.json', 'r') as f:
        existing_services = json.load(f)

if path.exists('services.txt'):
    logging.info('Reading new services from services.txt')
    with open('services.txt', 'r') as f:
        service_names = f.read().splitlines()

    # Regex to validate service name based on systemd documentation
    valid_service_name = re.compile('^[a-zA-Z0-9:_\-\.]+$')
    
    for name in service_names:
        name = name.strip()  # Trim white space
        if name:  # Check if name is empty
            if valid_service_name.match(name):
                if name not in existing_services:
                    logging.info(f'Adding new service: {name}')
                    existing_services[name] = {'status': 'unknown', 'alerted': True, 'previous_status': None}
            else:
                logging.info(f'Invalid service name: {name}. Skipping.')
        else:
            logging.info('Encountered a blank line. Skipping.')
    
    with open('services.json', 'w') as f:
        json.dump(existing_services, f)
    subprocess.run(['rm', 'services.txt'])

# Remove services listed in remove.txt
if path.exists('remove.txt'):
    logging.info('Reading services to remove from remove.txt')
    with open('remove.txt', 'r') as f:
        services_to_remove = f.read().splitlines()

    for service in services_to_remove:
        if service in existing_services:  # Changed from services_status
            logging.info(f'Removing service: {service}')
            del existing_services[service]  # Changed from services_status
    
    # Update JSON and remove remove.txt
    with open('services.json', 'w') as f:
        json.dump(existing_services, f)  # Changed from services_status
    subprocess.run(['rm', 'remove.txt'])

# Load existing service state
logging.info('Loading existing service state from services.json')
with open('services.json', 'r') as f:
    services_status = json.load(f)

# Initial alert check
logging.info('Performing initial alert check')
for service, attributes in services_status.items():
    result = subprocess.run(['systemctl', 'is-active', service], stdout=subprocess.PIPE)
    current_status = result.stdout.decode('utf-8').strip()
    if attributes['alerted'] is False and current_status == 'active':
        logging.info(f'Sending initial alert for {service}')
        requests.post(webhook_url, json={'text': f'Service {service} is active'})
        attributes['alerted'] = True
        with open('services.json', 'w') as f:
            json.dump(services_status, f)

# Main Monitoring Loop
logging.info('Entering main monitoring loop')
while True:
    updated = False
    num_services = len(services_status.keys())
    
    # Log and print that it's checking X number of services
    logging.info(f'Checking status for {num_services} services')

    for service, attributes in services_status.items():
        # Service State Check (without logging each service)
        result = subprocess.run(['systemctl', 'is-active', service], stdout=subprocess.PIPE)
        current_status = result.stdout.decode('utf-8').strip()
        
        # Alert Logic
        if current_status != attributes.get('previous_status', None):
            if current_status == 'active':
                logging.info(f'Sending alert: {service} is now active ✅')
                requests.post(webhook_url, json={'text': f'✅Service {service} is now active ✅'})
            else:
                logging.info(f'Sending alert: {service} is not active 🚨')
                requests.post(webhook_url, json={'text': f'🚨Service {service} is not active 🚨'})
                
            attributes['alerted'] = True  # Consider if you really need this line
            attributes['previous_status'] = current_status  # Update the previous_status field
            updated = True
 
        # Update service status
        if attributes['status'] != current_status:
            attributes['status'] = current_status
            updated = True
    
    # Update JSON File
    if updated:
        logging.info('Updating services.json')
        with open('services.json', 'w') as f:
            json.dump(services_status, f)
            
    # Loop Sleep
    logging.info(f'Sleeping for {loop_interval} seconds')
    time.sleep(loop_interval)
