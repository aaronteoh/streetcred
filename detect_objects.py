import os
import pathlib
from datetime import datetime
from logger import load_logger, logging


def check_dir_name(dir_name):
    try:
        datetime.strptime(dir_name, '%Y%m%d%H%M')
    except ValueError:
        return False
    else:
        return True


def load_image_into_numpy_array(path):
    img_data = tf.io.gfile.GFile(path, 'rb').read()
    image = Image.open(BytesIO(img_data))
    (im_width, im_height) = image.size

    return np.array(image.getdata()).reshape((im_height, im_width, 3)).astype(np.uint8)


def get_keypoint_tuples(eval_config):
    tuple_list = []
    kp_list = eval_config.keypoint_edge
    for edge in kp_list:
        tuple_list.append((edge.start, edge.end))

    return tuple_list


def load_label_map():
    label_map_path = os.path.join(proj_dir, 'object_detection/data/mscoco_label_map.pbtxt')
    label_map = label_map_util.load_labelmap(label_map_path)
    categories = label_map_util.convert_label_map_to_categories(label_map,
                                                                max_num_classes=label_map_util.get_max_label_map_index(label_map),
                                                                use_display_name=True)
    category_index = label_map_util.create_category_index(categories)

    return category_index


def load_model():
    model_name = 'centernet_resnet101_v1_fpn_512x512_coco17_tpu-8'
    pipeline_config = os.path.join(proj_dir, 'object_detection', 'test_data', model_name, 'pipeline.config')
    model_dir = os.path.join(proj_dir, 'object_detection', 'test_data', model_name, 'checkpoint')

    configs = config_util.get_configs_from_pipeline_file(pipeline_config)
    model_config = configs['model']
    # model_config.center_net.object_center_params.max_box_predictions = 200

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


def run_detections_for_dir(dir_name):
    logging.info('Running detections for %s'%dir_name)
    images = [x for x in os.listdir(os.path.join(images_dir, dir_name)) if x.endswith('.jpg')]
    compiled = []

    logging.info('%s images to process' % len(images))
    for image_file in images:
        logging.info('Processing %s.' % image_file)

        # possible to stack?
        image_path = os.path.join(images_dir, dir_name, image_file)
        image_np = load_image_into_numpy_array(image_path)
        input_tensor = tf.convert_to_tensor(np.expand_dims(image_np, 0), dtype=tf.float32)
        detections, predictions_dict, shapes = detect_fn(input_tensor)
        # / possible to stack?

        label_id_offset = 1
        for i in range(detections['num_detections'].numpy()[0]):
            object_class = category_index[detections['detection_classes'][:, i].numpy()[0] + label_id_offset]['name']
            score = detections['detection_scores'][:, i].numpy()[0]
            box = detections['detection_boxes'][:, i, :].numpy()[0]
            relative_size = (box[2] - box[0]) * (box[3] - box[1])

            compiled.append([image_file,
                             object_class,
                             score,
                             box[1], box[3], box[0], box[2],
                             relative_size])

    detections_path = os.path.join(detections_dir, '%s_detections.csv' % dir_name)
    pd.DataFrame(compiled, columns=['image', 'class', 'score', 'x1', 'x2', 'y1', 'y2', 'relative_size']).to_csv(detections_path, index=False)
    logging.info('Saved detections to %s' % detections_path)


def main():
    to_process = [dir_name for dir_name in os.listdir(images_dir) if check_dir_name(dir_name)]
    logging.info('%s directories to process'%len(to_process))

    for dir_name in to_process:
        run_detections_for_dir(dir_name)

        from_dir = os.path.join(images_dir, dir_name)
        to_dir = os.path.join(images_dir, 'p' + dir_name)
        os.rename(from_dir, to_dir)

        logging.info('Images moved from %s to %s'%(from_dir, to_dir))

if __name__ == '__main__':
    proj_dir = pathlib.Path(__file__).parent.absolute()
    filename = os.path.basename(__file__).split('.')[0]

    load_logger(proj_dir, filename)
    logging.info('>>> Script start')

    data_dir = os.path.join(proj_dir, 'data')
    images_dir = os.path.join(data_dir, 'images')
    detections_dir = os.path.join(data_dir, 'detections')

    import numpy as np
    import pandas as pd
    from PIL import Image
    from six import BytesIO
    import tensorflow as tf
    logging.info('Base libraries loaded')

    from object_detection.utils import config_util
    from object_detection.utils import label_map_util
    from object_detection.builders import model_builder
    logging.info('Object detection modules loaded')

    if not os.path.isdir(detections_dir):
        logging.info('Creating %s' % detections_dir)
        os.makedirs(detections_dir)

    detection_model, configs = load_model()
    detect_fn = get_model_detection_function(detection_model)
    logging.info('Model loaded.')

    category_index = load_label_map()
    logging.info('Label map loaded.')

    main()
    logging.info('Script complete')