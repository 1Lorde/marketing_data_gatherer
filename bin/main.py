import logging
import time
from datetime import datetime, timedelta

import schedule

from api_utils import get_campaigns, get_sources
from app import app
from bin.utils import remove_data_fetched_at, save_data_to_db, get_last_fetched, set_last_fetched
from models import db
from utils import set_fetched_at, read_config, init_logger


def job():
    campaigns = get_campaigns()
    sources = get_sources(campaigns)

    campaigns, sources, fetched_at = set_fetched_at(campaigns, sources)

    last_fetched_at = get_last_fetched()

    save_data_period_start = datetime(fetched_at.year, fetched_at.month, fetched_at.day, 1, 0, 0)
    save_data_period_end = datetime(fetched_at.year, fetched_at.month, fetched_at.day, 1, 1, 0)

    with app.test_request_context():
        db.init_app(app)

        if save_data_period_start <= fetched_at <= save_data_period_end:
            fetched_at = datetime(fetched_at.year, fetched_at.month, fetched_at.day, 0, 0, 0)
            fetched_at = fetched_at - timedelta(days=1)
            campaigns, sources, fetched_at = set_fetched_at(campaigns, sources, fetched_at)
            save_data_to_db(campaigns, sources)
        else:
            remove_data_fetched_at(last_fetched_at)
            save_data_to_db(campaigns, sources)
            set_last_fetched(fetched_at)

        print(campaigns)
        print(sources)


def main():
    read_config()
    init_logger()
    schedule.every(1).minutes.do(job)

    logging.info('Run data gathering script')
    job()
    while 1:
        schedule.run_pending()
        time.sleep(1)
