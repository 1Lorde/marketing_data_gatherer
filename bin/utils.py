import logging
from datetime import datetime

import yaml

from models import db, Campaign, Source

config = None


def read_config():
    global config
    with open("config.yml", "r") as ymlfile:
        config = yaml.load(ymlfile, Loader=yaml.FullLoader)


def init_logger():
    format = config['logging']['format']
    date_format = config['logging']['date_format']
    logging.basicConfig(level=logging.INFO, format=format, datefmt=date_format)


def set_fetched_at(campaigns, sources, fetched_at=None):
    if not fetched_at:
        fetched_at = datetime.now()

    for campaign in campaigns:
        campaign.fetched_at = fetched_at

    for source in sources:
        source.fetched_at = fetched_at

    return campaigns, sources, fetched_at


def set_last_fetched(fetched_at):
    with open('bin/last_fetched_at', 'w') as f:
        f.write(str(fetched_at))


def get_last_fetched():
    with open('bin/last_fetched_at', 'r') as f:
        try:
            return datetime.strptime(f.readline(), '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            return ''


def save_data_to_db(campaigns, sources):
    db.session.add_all(campaigns)
    db.session.add_all(sources)
    db.session.commit()


def remove_data_fetched_at(fetched_at):
    Campaign.query.filter_by(fetched_at=fetched_at).delete()
    Source.query.filter_by(fetched_at=fetched_at).delete()
    db.session.commit()
