import os
import pytz
import shutil
import logging
import pathlib
import requests
import pandas as pd
from PIL import Image
import urllib.request
from datetime import datetime
from json import JSONDecodeError


def load_logger():
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    tz = pytz.timezone('Singapore')
    log_path = os.path.join(log_dir, '%s-%s.log'%(datetime.now(tz).strftime('%Y%m%d'), os.path.basename(__file__).split('.')[0]))

    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename=log_path, level=logging.DEBUG)


def main():
    try:
        r = requests.get(url, headers=headers).json()['value']
    except JSONDecodeError as e:
        logging.exception("JSONDecodeError")
    else:
        logging.info('%s items found.'%len(r))
        path_split = r[0]['ImageLink'].split('?')[0].split('/')
        request_datetime = ('%s%s'%(path_split[3], path_split[4])).replace('-', '')
        dest_dir = os.path.join(images_dir, request_datetime)

        if os.path.isdir(dest_dir):
            logging.info('Deleting %s' % dest_dir)
            shutil.rmtree(dest_dir)

        os.makedirs(dest_dir)

        meta_df = []

        logging.info('Downloading images to %s'%dest_dir)
        for item in r:
            dest_path = os.path.join(dest_dir, item['ImageLink'].split('?')[0].split('/')[-1])
            urllib.request.urlretrieve(item['ImageLink'], dest_path)

            path_split = item['ImageLink'].split('?')[0].split('/')
            meta_data = [item['CameraID'],
                         item['Latitude'],
                         item['Longitude'],
                         path_split[3],
                         path_split[-1].split('_')[1],
                         path_split[-1],
                         Image.open(dest_path).size]

            meta_df.append(meta_data)


        if not os.path.isdir(metadata_dir):
            logging.info('Creating %s' % metadata_dir)
            os.makedirs(metadata_dir)
        metadata_path = os.path.join(metadata_dir, '%s_images.csv'%request_datetime)

        pd.DataFrame(meta_df, columns=['CameraID', 'Latitude', 'Longitude', 'Date', 'Time', 'Filename', 'Dimensions']).to_csv(metadata_path, index=False)
        logging.info('Saved metadata to %s'%metadata_path)



if __name__ == '__main__':
    data_dir = os.path.join(pathlib.Path(__file__).parent.absolute(), 'data')
    log_dir = os.path.join(data_dir, 'logs')
    images_dir = os.path.join(data_dir, 'images')
    metadata_dir = os.path.join(data_dir, 'metadata')

    load_logger()
    logging.info('Script start')
    url = 'http://datamall2.mytransport.sg/ltaodataservice/Traffic-Imagesv2'
    headers = {'AccountKey': os.environ['LTA-API-KEY']}
    main()
    logging.info('Script complete')