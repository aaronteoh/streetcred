import os
import json
import pytz
import pathlib
import requests
from datetime import datetime

proj_dir = pathlib.Path(__file__).parent.absolute()

with open(os.path.join(proj_dir, 'credentials/LTA-API-KEY'), 'r') as file:
    API_KEY = file.read().strip()
headers = {'AccountKey': API_KEY}

def get_full_data(url):
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