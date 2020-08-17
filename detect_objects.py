import os
import pathlib
from datetime import datetime
from logger import load_logger, logging


def load_model():
    model_name = 'centernet_resnet101_v1_fpn_512x512_coco17_tpu-8'
    pipeline_config = os.path.join(proj_dir, 'models/research/object_detection/test_data', model_name, 'pipeline.config')
    model_dir = os.path.join(proj_dir, 'models/research/object_detection/test_data', model_name, 'checkpoint')

    configs = config_util.get_configs_from_pipeline_file(pipeline_config)
    model_config = configs['model']
    model_config.center_net.object_center_params.max_box_predictions = 200

    detection_model = model_builder.build(model_config=model_config, is_training=False)
    ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
    ckpt.restore(os.path.join(model_dir, 'ckpt-0')).expect_partial()

    return detection_model, configs


def get_model_detection_function(model):
    @tf.function
    def detect_fn(image):
        image, shapes = model.preprocess(image)
        prediction_dict = model.predict(image, shapes)
        detections = model.postprocess(prediction_dict, shapes)

        return detections, prediction_dict, tf.reshape(shapes, [-1])

    return detect_fn


def main():
    completed_dirs = []
    for root, dirs, files in os.walk(metadata_dir):
        for file in files:
            completed_dirs.append(os.path.join(file)[:12])

    to_process = [dir_name for dir_name in os.listdir(images_dir) if check_dir_name(dir_name) and dir_name in completed_dirs]
    logging.info('%s directories to process'%len(to_process))

    for dir_name in to_process:
        detections_df = run_detections_for_dir(dir_name)
        aggregated_df = aggregate_detections(detections_df)
        compile_detections(aggregated_df, dir_name)
        clear_working_files(dir_name)


def check_dir_name(dir_name):
    try:
        datetime.strptime(dir_name, '%Y%m%d%H%M')
    except ValueError:
        return False
    else:
        return True


def run_detections_for_dir(dir_name):
    logging.info('Running detections for %s'%dir_name)
    images = [x for x in os.listdir(os.path.join(images_dir, dir_name)) if x.endswith('.jpg')]
    compiled = []

    logging.info('%s images to process' % len(images))
    for image_file in images:
        # possible to stack?
        image_path = os.path.join(images_dir, dir_name, image_file)
        image_np = load_image_into_numpy_array(image_path)
        input_tensor = tf.convert_to_tensor(np.expand_dims(image_np, 0), dtype=tf.float32)
        detections, predictions_dict, shapes = detect_fn(input_tensor)
        # / possible to stack?

        label_id_offset = 1
        for i in range(detections['num_detections'].numpy()[0]):
            score = detections['detection_scores'][:, i].numpy()[0]
            if score > .2:
                object_class = detections['detection_classes'][:, i].numpy()[0] + label_id_offset
                box = detections['detection_boxes'][:, i, :].numpy()[0]
                relative_size = (box[2] - box[0]) * (box[3] - box[1])

                compiled.append([image_file.split('.')[0],
                                 object_class,
                                 score,
                                 box[1], box[3], box[0], box[2],
                                 relative_size])

    if not os.path.isdir(detections_dir):
        os.makedirs(detections_dir)
        logging.info('Created %s' % detections_dir)

    detections_path = os.path.join(detections_dir, '%s_detections.csv' % dir_name)
    detections_df = pd.DataFrame(compiled, columns=['image', 'class', 'score', 'x1', 'x2', 'y1', 'y2', 'relative_size'])
    logging.info('Detections DF shape: %s' % str(detections_df.shape))
    detections_df.to_csv(detections_path, index=False, header=False)
    logging.info('Saved detections to %s' % detections_path)

    upload_blob(detections_path, 'detections/%s_detections.csv' % dir_name)
    os.remove(detections_path)
    logging.info('Deleted %s' % detections_path)

    return detections_df


def load_image_into_numpy_array(path):
    img_data = tf.io.gfile.GFile(path, 'rb').read()
    image = Image.open(BytesIO(img_data))
    (im_width, im_height) = image.size

    return np.array(image.getdata()).reshape((im_height, im_width, 3)).astype(np.uint8)


def upload_blob(source_file_name, destination_blob_name):
    bucket = storage_client.bucket('tyeoh-streetcred')
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)

    logging.info("File {} uploaded to {}.".format(source_file_name, destination_blob_name))


def aggregate_detections(detections_df):
    detections_df['rank'] = detections_df.groupby(by=['image', 'x1', 'x2', 'y1', 'y2'])['score'].transform(lambda x: x.rank(method='first', ascending=False))

    detections_df = detections_df[(detections_df['score'] > .3) &
                                  (detections_df['relative_size'] < .1) &
                                  (detections_df['rank'] == 1) &
                                  (detections_df['class'].isin([3,4,6,8]))][['image']]
    aggregated_df = detections_df.groupby('image').agg(Detections=('image', 'count')).reset_index()
    aggregated_df.drop_duplicates(inplace=True)
    logging.info('Aggregated DF shape: %s' % str(aggregated_df.shape))

    return aggregated_df


def compile_detections(aggregated_df, dir_name):
    metadata_path = os.path.join(metadata_dir, '%s_images.csv' % dir_name)
    metadata_df = pd.read_csv(metadata_path, names = ['CameraID', 'Latitude', 'Longitude', 'Date', 'Time', 'Filename', 'Dimensions']).drop_duplicates()

    combined = metadata_df.merge(aggregated_df, left_on='Filename', right_on='image', how='left').drop(columns=['image'])
    combined['Detections'].fillna(0, inplace=True)
    logging.info('Combined DF shape: %s' % str(combined.shape))

    if not os.path.isdir(aggregated_dir):
        os.makedirs(aggregated_dir)
        logging.info('Created %s' % aggregated_dir)

    aggregated_path = os.path.join(aggregated_dir, '%s_aggregated.csv' % dir_name)
    combined.to_csv(aggregated_path, index=False, header=False)
    logging.info('Saved aggregated data to %s' % aggregated_path)

    upload_blob(aggregated_path, 'aggregated/%s_aggregated.csv' % dir_name)
    os.remove(aggregated_path)
    logging.info('Deleted %s' % aggregated_path)


def clear_working_files(dir_name):
    images_path = os.path.join(images_dir, dir_name)
    shutil.rmtree(images_path)
    logging.info('Deleted %s' % images_path)

    metadata_path = os.path.join(metadata_dir, '%s_images.csv' % dir_name)
    os.remove(metadata_path)
    logging.info('Deleted %s' % metadata_path)


if __name__ == '__main__':
    proj_dir = pathlib.Path(__file__).parent.absolute()
    filename = os.path.basename(__file__).split('.')[0]

    load_logger(proj_dir, filename)
    logging.info('>>> Script start')

    try:
        data_dir = os.path.join(proj_dir, 'data')
        images_dir = os.path.join(data_dir, 'images')
        detections_dir = os.path.join(data_dir, 'detections')
        metadata_dir = os.path.join(data_dir, 'metadata')
        aggregated_dir = os.path.join(data_dir, 'aggregated')

        import sys
        import shutil
        import numpy as np
        import pandas as pd
        from PIL import Image, ImageFile
        ImageFile.LOAD_TRUNCATED_IMAGES = True

        from six import BytesIO
        import tensorflow as tf
        logging.info('Base libraries loaded')

        sys.path.append('/models/research')
        from object_detection.utils import config_util
        from object_detection.builders import model_builder
        logging.info('Object detection modules loaded')

        from google.cloud import storage
        key_path = os.path.join(pathlib.Path(__file__).parent.absolute(), 'credentials','tyeoh-cloud-da52d6b77ebd.json')
        storage_client = storage.Client.from_service_account_json(key_path)

        detection_model, configs = load_model()
        detect_fn = get_model_detection_function(detection_model)
        logging.info('Model loaded.')

        main()
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
    else:
        logging.info('Script complete')