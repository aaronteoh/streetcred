import os, pathlib
from logger import load_logger, logging


def generate_detections_df(detections_files):
    detections_df = None

    for detections_file in detections_files:
        logging.info('Processing %s' % detections_file)
        df = pd.read_csv(os.path.join(detections_dir, detections_file))
        ###
        # remove overlappint detections
        ###
        if detections_df is None:
            detections_df = df
        else:
            detections_df = pd.concat([detections_df, df])

    detections_df = detections_df[(detections_df['score'] > .3) &
                                  (detections_df['relative_size'] < .1) &
                                  (detections_df['class'].isin(['car', 'truck', 'motorcycle', 'bus']))][['image']]
    detections_df = detections_df.groupby('image').agg(Detections=('image', 'count')).reset_index()

    return detections_df.drop_duplicates()


def generate_metatdata_df(metadata_files):
    metadata_df = None

    for metadata_file in metadata_files:
        logging.info('Processing %s' % metadata_file)
        df = pd.read_csv(os.path.join(metadata_dir, metadata_file))
        if metadata_df is None:
            metadata_df = df
        else:
            metadata_df = pd.concat([metadata_df, df])

    return metadata_df.drop_duplicates()


def main():
    detections_files = [x for x in os.listdir(detections_dir) if x.endswith('_detections.csv')]
    detections_df = generate_detections_df(detections_files)
    logging.info('Detections DF generated')

    metadata_files = [x for x in os.listdir(metadata_dir) if x.endswith('_images.csv')]
    metadata_df = generate_metatdata_df(metadata_files)
    logging.info('Metadata DF generated')

    combined = metadata_df.merge(detections_df, left_on='Filename', right_on='image', how='left').drop(columns=['image'])
    combined['Detections'].fillna(0, inplace=True)
    logging.info('Combined DF shape: %s'%str(combined.shape))
    aggregated_path = os.path.join(aggregated_dir, 'aggregated.csv')
    combined.to_csv(aggregated_path, index=False)
    logging.info('Saved aggregated data to %s'%aggregated_path)


if __name__ == '__main__':
    proj_dir = pathlib.Path(__file__).parent.absolute()
    filename = os.path.basename(__file__).split('.')[0]

    load_logger(proj_dir, filename)
    logging.info('>>> Script start')

    import os
    import pathlib
    import pandas as pd

    data_dir = os.path.join(proj_dir, 'data')
    metadata_dir = os.path.join(data_dir, 'metadata')
    detections_dir = os.path.join(data_dir, 'detections')
    aggregated_dir = os.path.join(data_dir, 'aggregated')

    if not os.path.isdir(aggregated_dir):
        logging.info('Creating %s' % aggregated_dir)
        os.makedirs(aggregated_dir)

    logging.info('Packages and directories loaded')

    main()
    logging.info('Script complete')


