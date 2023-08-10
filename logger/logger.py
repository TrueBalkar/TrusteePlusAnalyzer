import logging
from configs import *

levels = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


class Logger:
    def __init__(self):
        self.level = logging.INFO
        self.filename = CONFIGS['Service']['LogsPath']
        self.filemode = 'w'
        self.format = '%(asctime)s:%(levelname)s:%(message)s'
        self.datefmt = '%d-%b-%y %H:%M:%S'

    def start_logger(self):
        logging.basicConfig(level=self.level,
                            filename=self.filename,
                            filemode=self.filemode,
                            format=self.format,
                            datefmt=self.datefmt)
        logging.critical('[NEW SESSION STARTED]~red')
