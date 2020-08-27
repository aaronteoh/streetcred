import pathlib, os
import pandas as pd

app_dir = pathlib.Path(__file__).parent.absolute()
proj_dir = app_dir
while True:
    parent, subdir = os.path.split(proj_dir)
    if subdir == 'streetcred':
        break
    else:
        proj_dir = parent

from object_detection.utils import label_map_util
label_map_path = os.path.join(proj_dir, 'models/research/object_detection/data/mscoco_label_map.pbtxt')
label_map = label_map_util.load_labelmap(label_map_path)
categories = label_map_util.convert_label_map_to_categories(label_map,
                                                            max_num_classes=label_map_util.get_max_label_map_index(label_map),
                                                            use_display_name=True)

labels_list = []
for item in categories:
    labels_list.append([item['id'], item['name']])

labels_df = pd.DataFrame(labels_list, columns=['id', 'name'])

labels_df.to_csv(os.path.join(app_dir, 'metadata', 'traffic_images-label_map.csv'), index=False)