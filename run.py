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
import shutil

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings('ignore')

from scanner.app_scanner import AppScanner

AppScanner = AppScanner()
if os.path.exists(AppScanner.template_path):
    logging.info('Found old template!~red')
    for second in range(15, 0, -1):
        logging.info(f'Deleting old template in {second} sec(s)~red')
        time.sleep(1)
    logging.info('Deleting old template...~red')
    shutil.rmtree(AppScanner.template_path)
    logging.info('Old template deleted successfully!~green')
logging.info('Creating new template directory...~red')
os.makedirs(AppScanner.template_path)
logging.info(f'Template directories with path: {AppScanner.template_path} created successfully!~green')

AppScanner.prepare_apps()
logging.info('Initiating scan...~green')
AppScanner.start_scanner()
logging.info('Scanning completed!~green')
