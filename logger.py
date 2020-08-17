import os
import sys
import pytz
import logging
from datetime import datetime

def load_logger(proj_dir, filename):
    log_dir = os.path.join(proj_dir, 'data', 'logs')

    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    tz = pytz.timezone('Singapore')
    log_path = os.path.join(log_dir, '%s-%s.log'%(datetime.now(tz).strftime('%Y%m%d'), filename))

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    output_file_handler = logging.FileHandler(log_path)
    stdout_handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    output_file_handler.setFormatter((formatter))
    stdout_handler.setFormatter(formatter)

    logger.addHandler(output_file_handler)
    logger.addHandler(stdout_handler)