import os, sys, pathlib, pytz
from datetime import datetime

tz = pytz.timezone('Singapore')

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


if __name__ == '__main__':
    from logger import load_logger, logging
    load_logger(app_dir, filename)
    logging.info('>>> Script start')

    try:
        log_dirs = []
        for root, dirs, files in os.walk(os.path.join(proj_dir), topdown=False):
            for name in dirs:
                if name == 'logs':
                    log_dirs.append(os.path.join(root, name))

        current_date = datetime.now(tz)

        for dir in log_dirs:
            for log_file in os.listdir(dir):
                log_date = log_file[:8]
                try:
                    log_date = datetime.strptime(log_date + '+0800', '%Y%m%d%z')
                except ValueError:
                    pass
                else:
                    days_diff = (current_date-log_date).days
                    if days_diff > 60:
                        os.remove(os.path.join(dir, log_file))
                        logging.info('%s removed'%os.path.join(dir, log_file))
    except Exception as e:
        logging.error("Exception occurred", exc_info=True)
    else:
        logging.info('Script complete')