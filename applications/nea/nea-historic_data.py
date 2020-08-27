import os
import pathlib
import requests
import pandas as pd
from logger import load_logger, logging
from datetime import datetime, timedelta


class nea_downloader:
    def __init__(self, api):
        if api not in ['uv-index', 'psi', '2-hour-weather-forecast', 'pm25', 'air-temperature']:
            raise AssertionError('Selected api is not one of values: \'uv-index\', \'psi\', \'2-hour-weather-forecast\', \'pm25\', \'air-temperature\'.')
        self.url = 'https://api.data.gov.sg/v1/environment/' + api
        self.api = api
        self.records = pd.DataFrame()
        self.metadata = pd.DataFrame()

    def download_daterange(self, start_date, end_date):
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')

        for n in range(int((self.end_date - self.start_date).days)+1):
            run_date = (self.start_date + timedelta(n)).strftime('%Y-%m-%d')
            self.download_date(run_date)

    def download_date(self, date):
        logging.info('Processing %s data for %s'%(self.api, date))
        date_items = []
        date_metadata = []

        r = requests.get(self.url, params={'date': date})
        items = r.json()['items']
        if self.api == 'air-temperature':
            metadata = r.json()['metadata']['stations']
        elif self.api in ['pm25', 'psi']:
            metadata = r.json()['region_metadata']
        elif self.api == '2-hour-weather-forecast':
            metadata = r.json()['area_metadata']
        else:
            metadata = None

        if self.api != 'uv-index':
            for item in items:
                if self.api == 'air-temperature':
                    timestamp = item['timestamp']
                    for reading in item['readings']:
                        station_id = reading['station_id']
                        value = reading['value']
                        date_items.append([station_id, timestamp, value])
                elif self.api == 'psi':
                    for region in ['central', 'east', 'national', 'north', 'south', 'west']:
                        record = [region]
                        record.append(item['timestamp'])
                        for reading in ['co_eight_hour_max', 'co_sub_index',
                                        'no2_one_hour_max',
                                        'o3_eight_hour_max', 'o3_sub_index',
                                        'pm10_sub_index', 'pm10_twenty_four_hourly',
                                        'pm25_sub_index', 'pm25_twenty_four_hourly',
                                        'psi_twenty_four_hourly',
                                        'so2_sub_index', 'so2_twenty_four_hourly']:
                            record.append(item['readings'][reading][region])
                        date_items.append(record)
                elif self.api == 'pm25':
                    for region in ['central', 'east', 'north', 'south', 'west']:
                        record = [region]
                        record.append(item['timestamp'])
                        record.append(item['readings']['pm25_one_hourly'][region])
                        date_items.append(record)
                elif self.api == '2-hour-weather-forecast':
                    timestamp = item['timestamp']
                    valid_period_start = item['valid_period']['start']
                    valid_period_end = item['valid_period']['end']
                    for forecast in item['forecasts']:
                        area = forecast['area']
                        forecast = forecast['forecast']
                        date_items.append([area, timestamp, valid_period_start, valid_period_end, forecast])

            for metadata_record in metadata:
                if self.api == 'air-temperature':
                    date_metadata.append([metadata_record['id'],
                                          metadata_record['name'],
                                          metadata_record['location']['latitude'],
                                          metadata_record['location']['longitude']])
                elif self.api in ['psi', 'pm25', '2-hour-weather-forecast']:
                    date_metadata.append([metadata_record['name'],
                                          metadata_record['label_location']['latitude'],
                                          metadata_record['label_location']['longitude']])

        elif self.api == 'uv-index':
            longest_seq = 0
            for item in items:
                if len(item['index'])>longest_seq:
                    longest_seq = len(item['index'])
                    date_items = []
                    for record in item['index']:
                        date_items.append([record['timestamp'], record['value']])


        date_records_df = pd.DataFrame(date_items)
        if self.api in ['air-temperature', 'psi', 'pm25', '2-hour-weather-forecast'] and len(date_metadata)>0:
            date_metadata_df = pd.DataFrame(date_metadata)
            self.metadata = pd.concat([self.metadata, date_metadata_df]).drop_duplicates()
        #     date_records_df = date_records_df.merge(date_metadata_df, how='left', on = 0)

        self.records = pd.concat([self.records, date_records_df])

    def save_data(self, data_dir):
        file_dir = os.path.join(data_dir, 'nea-%s'%self.api)
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)
            logging.info('Created %s' % file_dir)

        filename = '%s-%s_%s.csv'%(self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d'), self.api)
        self.records.to_csv(os.path.join(file_dir, filename), header=False, index=False)

    def save_metadata(self, data_dir):
        file_dir = os.path.join(data_dir, 'nea-%s'%self.api)
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)
            logging.info('Created %s' % file_dir)

        filename = '%s-metadata.csv'%(self.api)
        self.metadata.to_csv(os.path.join(file_dir, filename), header=False, index=False)



if __name__ == '__main__':
    start_date = '2017-01-01'
    end_date = '2017-01-31'

    app_dir = pathlib.Path(__file__).parent.absolute()
    filename = os.path.basename(__file__).split('.')[0]

    proj_dir = app_dir
    while True:
        parent, subdir = os.path.split(proj_dir)
        if subdir == 'streetcred':
            break
        else:
            proj_dir = parent

    load_logger(app_dir, filename)
    logging.info('>>> Script start')

    try:
        data_dir = os.path.join(app_dir, 'data')
        for api in ['uv-index', 'psi', '2-hour-weather-forecast', 'pm25', 'air-temperature']:
            logging.info('Running script for %s API from %s to %s'%(api, start_date, end_date))
            downloader = nea_downloader(api)
            downloader.download_daterange(start_date, end_date)
            downloader.save_data(data_dir)
            downloader.save_metadata(data_dir)
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
        raise
    else:
        logging.info('Script complete')