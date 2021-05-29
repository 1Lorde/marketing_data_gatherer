import logging
from logging import INFO
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

import yaml

config = None


def read_config():
    global config
    with open("utils/config.yml", "r") as ymlfile:
        config = yaml.load(ymlfile, Loader=yaml.FullLoader)
    return config


def init_logger():
    format = config['logging']['format']
    date_format = config['logging']['date_format']
    logging.basicConfig(level=logging.DEBUG, format=format, datefmt=date_format)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


class InfoTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename: str, when: str, interval: int):
        super().__init__(filename, when, interval)

    def emit(self, record):
        if not record.levelno == INFO:
            return
        super().emit(record)


def init_file_logger():
    format = config['logging']['file_format']
    date_format = config['logging']['file_date_format']
    logname = "logs/rules.log"
    handler = InfoTimedRotatingFileHandler(logname, when="midnight", interval=1)
    handler.suffix = "%Y%m%d"
    logger = logging.getLogger()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(fmt=format, datefmt=date_format))
    logger.addHandler(handler)
