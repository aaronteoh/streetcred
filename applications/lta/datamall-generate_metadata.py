import os
import sys
import json
import pytz
import pathlib
import pandas as pd
from datetime import datetime

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

    'carpark-availability': {'url': 'http://datamall2.mytransport.sg/ltaodataservice/CarParkAvailabilityv2',
                             'fields': [    'Agency',
                                            'Area',
                                            'CarParkID',
                                            'Development',
                                            'Location',
                                            'LotType'
                                            ],
                             'columns': [   'Timestamp',
                                            'Agency',
                                            'Area',
                                            'CarParkID',
                                            'Development',
                                            'Location',
                                            # 'Latitude', 'Longitude',
                                            'LotType'
                                            ]
                             },

    'traffic-speed-bands': {'url': 'http://datamall2.mytransport.sg/ltaodataservice/TrafficSpeedBandsv2',
                            'fields': ['LinkID',
                                       'Location',
                                       'RoadCategory',
                                       'RoadName',
                                        ],
                            'columns': ['Timestamp',
                                        'LinkID',
                                        'Latitude1', 'Longitude1',
                                        'Latitude2', 'Longitude2',
                                        'RoadCategory',
                                        'RoadName',
                                        ]
                            },
}

def generate_table(api):
    data, records_count = datamall_load(apis[api]['url'])
    logging.info('%s records found'%records_count)
    compiled = []
    for record_set in data:
        for timestamp in record_set:
            for record in record_set[timestamp]:
                row = [timestamp]
                for field in apis[api]['fields']:
                    if field != 'Location' or api != 'traffic-speed-bands': #not splitting carpark availability latlon for now as some missing
                        row.append(record[field])
                    else:
                        row += [float(x) for x in record[field].split(' ')]

                compiled.append(row)
    return pd.DataFrame(compiled, columns = apis[api]['columns'])


if __name__ == '__main__':
    load_logger(app_dir, filename)
    logging.info('>>> Script start')

    try:
        from google.cloud import storage
        key_path = os.path.join(proj_dir, 'credentials', 'GOOGLE-CLOUD-CREDENTIALS.json')
        storage_client = storage.Client.from_service_account_json(key_path)
        with open(key_path, 'r') as f:
            project_id = json.load(f)['project_id']
        bucket = storage_client.bucket('tyeoh-streetcred', user_project=project_id)

        metadata_dir = os.path.join(app_dir, 'metadata')

        if not os.path.isdir(metadata_dir):
            os.makedirs(metadata_dir)
            logging.info('Created %s' % metadata_dir)

        for api in apis:
            logging.info('Loading data for %s' % api)
            request_date = datetime.now(tz=pytz.timezone('Singapore')).strftime('%Y%m%d')
            df = generate_table(api)
            dest_path = os.path.join(metadata_dir, '%s_%s_metadata.csv.xz' % (request_date, api))
            df.to_csv(dest_path, index=False, header=True, compression='xz')
            logging.info('Saved data to %s'%dest_path)

            upload_blob(bucket, dest_path, '%s_metadata/%s_%s_metadata.csv.xz' % (api, request_date, api))
            os.remove(dest_path)
            logging.info('Deleted %s' % dest_path)

    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        raise
    else:
        logging.info('Script complete')