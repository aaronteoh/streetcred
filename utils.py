import os
import json
import pytz
import pathlib
import requests
from datetime import datetime
from logger import logging

proj_dir = pathlib.Path(__file__).parent.absolute()

with open(os.path.join(proj_dir, 'credentials/LTA-API-KEY'), 'r') as file:
    API_KEY = file.read().strip()
headers = {'AccountKey': API_KEY}

def datamall_load(url):
    full_data = []
    records_count = 0
    end_of_resp = False
    skip = 0
    while not end_of_resp:
        try:
            timestamp = datetime.now(tz=pytz.timezone('Singapore')).strftime('%Y-%m-%d %H:%M:%S')
            r = requests.get(url, params={'$skip': skip}, headers=headers)
            values = r.json()['value']

        except json.JSONDecodeError as e:
            print(e)
            raise

        else:
            full_data.append({timestamp: values})
            records_count += len(values)
            skip += 500
            if len(r.json()['value']) != 500:
                end_of_resp = True

    return full_data, records_count



def upload_blob(storage_client, source_file_name, destination_blob_name):
    bucket = storage_client.bucket('tyeoh-streetcred')
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)

    logging.info("File {} uploaded to {}".format(source_file_name, destination_blob_name))
