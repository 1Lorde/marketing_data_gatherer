import logging
import time
from datetime import datetime, timedelta

import schedule as schedule

from gatherer.utils import set_fetched_at, get_last_fetched, save_data_to_db, remove_data_fetched_at, set_last_fetched, \
    campaigns_to_daily, campaigns_to_extracted, sources_to_extracted, remove_extracted_data, sources_to_daily
from models.models import db
from run_web import app
from utils.api_utils import ApiUtils
from utils.utils import read_config, init_logger

api = None


def live_job():
    campaigns = api.get_campaigns()
    sources = api.get_sources(campaigns)

    campaigns, sources, fetched_at = set_fetched_at(campaigns, sources)

    last_fetched_at = get_last_fetched()

    save_data_period_start = datetime(fetched_at.year, fetched_at.month, fetched_at.day, 1, 0, 0)
    save_data_period_end = datetime(fetched_at.year, fetched_at.month, fetched_at.day, 1, 1, 0)

    with app.test_request_context():
        db.init_app(app)

        if save_data_period_start <= fetched_at <= save_data_period_end:
            fetched_at = datetime(fetched_at.year, fetched_at.month, fetched_at.day, 0, 0, 0)
            fetched_at = fetched_at - timedelta(days=1)
            daily_campaigns = campaigns_to_daily(campaigns)
            daily_sources = sources_to_daily(sources)

            daily_campaigns, daily_sources, fetched_at = \
                set_fetched_at(daily_campaigns, daily_sources, fetched_at)

            save_data_to_db(daily_campaigns, daily_sources)
        else:
            remove_data_fetched_at(last_fetched_at)
            save_data_to_db(campaigns, sources)
            set_last_fetched(fetched_at)

        print(campaigns)
        print(sources)

        api.check_rules()


def extract_job():
    with app.test_request_context():
        db.init_app(app)
        remove_extracted_data()

    for days in range(0, 30):
        end = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(1)
        start = end - timedelta(days)

        logging.info(f'Extracting campaigns for last {days + 1} days')
        campaigns = api.get_campaigns(start, end)
        extracted_campaigns = campaigns_to_extracted(campaigns, days + 1)

        logging.info(f'Extracting sources for last {days + 1} days')
        sources = api.get_sources(campaigns, start, end)
        extracted_sources = sources_to_extracted(sources, days + 1)

        set_fetched_at(extracted_campaigns, extracted_sources)

        with app.test_request_context():
            db.init_app(app)
            save_data_to_db(extracted_campaigns, extracted_sources)

        print(extracted_campaigns)
        print(extracted_sources)
        time.sleep(7)


if __name__ == '__main__':
    config = read_config()
    api = ApiUtils(config)
    init_logger()

    schedule.every(1).minutes.do(live_job)
    schedule.every().day.at("01:10").do(extract_job)

    logging.info('Run data gathering script')
    extract_job()
    live_job()
    while 1:
        schedule.run_pending()
        time.sleep(1)
