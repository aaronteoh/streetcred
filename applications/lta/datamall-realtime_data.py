import os, pathlib, sys
from datetime import datetime
import pytz
import pandas as pd

app_dir = pathlib.Path(__file__).parent.absolute()
filename = os.path.basename(__file__).split('.')[0]

proj_dir = app_dir
while True:
    parent, subdir = os.path.split(proj_dir)
    if subdir == 'streetcred':
        break
    else:
        proj_dir = parent

sys.path.append(proj_dir)
from logger import load_logger, logging
from utils import datamall_load, upload_blob


apis = {
    'taxi-availability': {'url': 'http://datamall2.mytransport.sg/ltaodataservice/Taxi-Availability',
                          'fields': ['Latitude', 'Longitude']
                          },
    'carpark-availability': {'url': 'http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2',
                             'fields': ['AvailableLots', 'CarParkID']
                             },
    'traffic-incidents': {'url': 'http://datamall2.mytransport.sg/ltaodataservice/TrafficIncidents',
                          'fields': ['Latitude', 'Longitude', 'Message', 'Type']
                          },
    'traffic-speed-bands': {'url': 'http://datamall2.mytransport.sg/ltaodataservice/TrafficSpeedBandsv2',
                            'fields': ['LinkID', 'MinimumSpeed']
                            },
}


def generate_table(api):
    data, records_count = datamall_load(apis[api]['url'])
    logging.info('%s records found'%records_count)
    compiled = []
    for record_set in data:
        for timestamp in record_set:
            timestamp_abbr = timestamp.split(' ')[-1]
            for record in record_set[timestamp]:
                row = [timestamp_abbr]
                for field in apis[api]['fields']:
                    row.append(record[field])
                compiled.append(row)

    return pd.DataFrame(compiled)


def main():
    for api in apis:
        logging.info('Loading data for %s'%api)
        request_datetime = datetime.now(tz=pytz.timezone('Singapore')).strftime('%Y%m%d%H%M')
        df = generate_table(api)
        dest_dir = os.path.join(data_dir, api)
        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir)
            logging.info('Created %s' % dest_dir)
        dest_path = os.path.join(dest_dir, '%s_%s.csv'%(request_datetime, api))
        df.to_csv(dest_path, index=False, header=False)
        logging.info('Saved data to %s'%dest_path)

        upload_blob(storage_client, dest_path, '%s/%s_%s.csv' % (api, request_datetime, api))
        os.remove(dest_path)
        logging.info('Deleted %s' % dest_path)


if __name__ == '__main__':
    load_logger(app_dir, filename)
    logging.info('>>> Script start')

    try:
        from google.cloud import storage
        key_path = os.path.join(proj_dir, 'credentials', 'GOOGLE-CLOUD-CREDENTIALS.json')
        storage_client = storage.Client.from_service_account_json(key_path)

        data_dir = os.path.join(app_dir, 'data')
        if not os.path.isdir(data_dir):
            os.makedirs(data_dir)
            logging.info('Created %s' % data_dir)
        main()
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        raise
    else:
        logging.info('Script complete')
