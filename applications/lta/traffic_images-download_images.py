import os, pathlib, sys

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

            # add retry here
            urllib.request.urlretrieve(item['ImageLink'], dest_path)

            path_split = item['ImageLink'].split('?')[0].split('/')
            meta_data = [item['CameraID'],
                         item['Latitude'],
                         item['Longitude'],
                         path_split[3],
                         path_split[-1].split('_')[1],
                         path_split[-1].split('.')[0],
                         Image.open(dest_path).size]

            meta_df.append(meta_data)

        metadata_dir = os.path.join(data_dir, 'traffic-images-metadata')

        if not os.path.isdir(metadata_dir):
            logging.info('Creating %s' % metadata_dir)
            os.makedirs(metadata_dir)
        metadata_path = os.path.join(metadata_dir, '%s_images.csv'%request_datetime)

        pd.DataFrame(meta_df, columns=['CameraID', 'Latitude', 'Longitude', 'Date', 'Time', 'Filename', 'Dimensions']).to_csv(metadata_path, index=False, header=False)
        logging.info('Saved metadata to %s'%metadata_path)



if __name__ == '__main__':
    load_logger(app_dir, filename)
    logging.info('>>> Script start')
    try:
        import shutil
        import requests
        import pandas as pd
        from PIL import Image
        import urllib.request
        from json import JSONDecodeError

        data_dir = os.path.join(app_dir, 'data')
        images_dir = os.path.join(data_dir, 'traffic-images-raw')

        url = 'http://datamall2.mytransport.sg/ltaodataservice/Traffic-Imagesv2'
        with open(os.path.join(proj_dir, 'credentials/LTA-API-KEY'), 'r') as file:
            API_KEY = file.read().strip()
        headers = {'AccountKey': API_KEY}
        main()
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
    else:
        logging.info('Script complete')