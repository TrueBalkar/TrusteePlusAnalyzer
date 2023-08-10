import logging
from logger.logger import Logger
import time
logger = Logger()
logger.start_logger()

seconds = 5
for second in range(seconds):
    logging.info(f'You have {seconds-second} second(s) to prepare!~yellow')
    time.sleep(1)
logging.info('Starting analyzer...~green')
logging.info('Loading weights for keras_ocr: craft_mtl_25k.h5, crnn_kurapan.h5...~green')

import os
import warnings

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings('ignore')

from scanner.app_scanner import AppScanner

AppScanner = AppScanner()
if not os.path.exists(AppScanner.template_path):
    logging.info('Template directory not found... Creating new template directory...~red')
    os.makedirs(AppScanner.template_path)
    logging.info(f'Template directories with path: {AppScanner.template_path} created successfully!~green')

main_template_status = {
    'templates.json': False,
    'market': False,
    'settings': False,
    'wallet': False
}

for filename in os.listdir(AppScanner.template_path):
    if filename in main_template_status.keys():
        main_template_status[filename] = True

AppScanner.prepare_apps()
if not all(main_template_status.values()):
    logging.info('Main template not found!~red')
    logging.info('Initiating creation of new main template...~yellow')
    logging.info('Main template created!~green')
logging.info('Main template found!~green')
logging.info('Initiating analysis...~green')
AppScanner.start_scanner()
logging.info('Analysis completed!~green')
