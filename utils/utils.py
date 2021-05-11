import logging

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
    logging.basicConfig(level=logging.INFO, format=format, datefmt=date_format)
