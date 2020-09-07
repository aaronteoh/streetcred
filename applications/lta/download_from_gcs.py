import os, pathlib
from datetime import datetime, timedelta
import json

app_dir = pathlib.Path(__file__).parent.absolute()
filename = os.path.basename(__file__).split('.')[0]

proj_dir = app_dir
while True:
    parent, subdir = os.path.split(proj_dir)
    if subdir == 'streetcred':
        break
    else:
        proj_dir = parent


from google.cloud import storage
key_path = os.path.join(proj_dir, 'credentials', 'GOOGLE-CLOUD-CREDENTIALS.json')
storage_client = storage.Client.from_service_account_json(key_path)

with open(key_path, 'r') as f:
    project_id = json.load(f)['project_id']
bucket = storage_client.bucket('tyeoh-streetcred', user_project=project_id)

# https://cloud.google.com/storage/docs/listing-objects#code-samples
def list_blobs(dataset):
    blobs = bucket.list_blobs(prefix=dataset)
    return sorted([blob.name for blob in blobs])


# https://cloud.google.com/storage/docs/downloading-objects#storage-download-object-python
# https://cloud.google.com/storage/docs/using-requester-pays#storage-download-file-requester-pays-python
def download_blob(source_blob_name, destination_file_name):
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(
        "Blob {} downloaded to {}.".format(
            source_blob_name, destination_file_name
        )
    )

def download_data(dataset, destination_dir, start_date, end_date, review_only=False):
    assert dataset in datasets
    try:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        assert end_datetime>=start_datetime
    except ValueError as e:
        raise e
    except AssertionError as e:
        print('Start date later than end date.')
        raise e
    if not os.path.isdir(destination_dir):
        print('Creating %s' % destination_dir)
        os.makedirs(destination_dir)
    all_blobs = [x.split('/')[-1] for x in list_blobs(dataset)]

    for n in range(int((end_datetime - start_datetime).days) + 1):
        run_date = (start_datetime + timedelta(n)).strftime('%Y%m%d')
        to_download = [x for x in all_blobs if x.startswith(run_date) and x.endswith('_%s.csv.xz'%datasets[dataset])]
        print('[%s] %s: %s files found'%(run_date, dataset, len(to_download)))

        if not review_only:
            for file in to_download:
                source = '%s/%s'%(dataset, file)
                destination = os.path.join(destination_dir, file)
                download_blob(source, destination)

if __name__ == '__main__':

    start_date = 'YYYY-MM-DD'
    end_date = 'YYYY-MM-DD'

    # comment out datasets not required
    datasets = {
                'carpark-availability': 'carpark-availability',
                'taxi-availability': 'taxi-availability',
                'traffic-incidents': 'traffic-incidents',
                'traffic-speed-bands': 'traffic-speed-bands',
                'traffic-images-aggregated': 'aggregated',
                'traffic-images-detections': 'detections'
                }

    for dataset in datasets:
        destination_dir = os.path.join(app_dir, 'downloads', dataset)
        download_data(dataset, destination_dir, start_date, end_date, review_only=True)