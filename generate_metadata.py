import os
import pathlib
import pandas as pd
from utils import get_full_data

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
    data, records_count = get_full_data(apis[api]['url'])
    print('%s records found'%records_count)
    compiled = []
    for record_set in data:
        for timestamp in record_set:
            for record in record_set[timestamp]:
                row = [timestamp]
                for field in apis[api]['fields']:
                    if api != 'traffic-speed-bands' or field != 'Location':
                        row.append(record[field])
                    else:
                        row += [float(x) for x in record[field].split(' ')]

                compiled.append(row)
    return pd.DataFrame(compiled, columns = apis[api]['columns'])


proj_dir = pathlib.Path(__file__).parent.absolute()
metadata_dir = os.path.join(proj_dir, 'metadata')

if not os.path.isdir(metadata_dir):
    os.makedirs(metadata_dir)
    print('Created %s' % metadata_dir)

for api in apis:
    print('Loading data for %s' % api)
    df = generate_table(api)
    dest_path = os.path.join(metadata_dir, '%s_metadata.csv'%api)
    df.to_csv(dest_path, index=False, header=True)
    print('Saved data to %s'%dest_path)