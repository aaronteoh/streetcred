import os
import pytz
import logging
from datetime import datetime

def load_logger(proj_dir, filename):
    log_dir = os.path.join(proj_dir, 'data', 'logs')

    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    tz = pytz.timezone('Singapore')
    log_path = os.path.join(log_dir, '%s-%s.log'%(datetime.now(tz).strftime('%Y%m%d'), filename))

    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename=log_path, level=logging.DEBUG)