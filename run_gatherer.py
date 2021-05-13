import logging
import time
from datetime import datetime, timedelta

import schedule as schedule

from gatherer.utils import set_fetched_at, get_last_fetched, save_data_to_db, remove_data_fetched_at, set_last_fetched, \
    campaigns_to_daily, campaigns_to_extracted, sources_to_extracted, sources_to_daily, remove_daily_data
from models.models import db, DailyCampaign
from run_web import app
from utils.api_utils import ApiUtils
from utils.utils import read_config, init_logger

api = None


def live_job():
    campaigns = api.get_campaigns()
    sources = api.get_sources(campaigns)

    campaigns, sources, fetched_at = set_fetched_at(campaigns, sources)
    last_fetched_at = get_last_fetched()

    with app.test_request_context():
        db.init_app(app)

        remove_data_fetched_at(last_fetched_at)
        save_data_to_db(campaigns, sources)
        set_last_fetched(fetched_at)

        print(campaigns)
        print(sources)

        api.check_campaign_rules()


def daily_job():
    now = datetime.now()
    yesterday = datetime(now.year, now.month, now.day, 0, 0, 0) - timedelta(1)

    campaigns = api.get_campaigns(start_date=yesterday, end_date=yesterday)
    sources = api.get_sources(campaigns, start_date=yesterday, end_date=yesterday)

    with app.test_request_context():
        db.init_app(app)
        daily_campaigns = campaigns_to_daily(campaigns)
        daily_sources = sources_to_daily(sources)

        daily_campaigns, daily_sources, fetched_at = \
            set_fetched_at(daily_campaigns, daily_sources, yesterday)

        save_data_to_db(daily_campaigns, daily_sources)

        last_day = yesterday - timedelta(30)
        DailyCampaign.query.filter_by(fetched_at=last_day).delete()
        db.session.commit()


def extract_last_month_job():
    with app.test_request_context():
        db.init_app(app)
        remove_daily_data()

    for days in range(1, 30):
        date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days)

        logging.info(f'Extracting campaigns for {date}')
        campaigns = api.get_campaigns(date, date)

        logging.info(f'Extracting sources for {date}')
        sources = api.get_sources(campaigns, date, date)

        daily_campaigns = campaigns_to_daily(campaigns)
        daily_sources = sources_to_daily(sources)

        daily_campaigns, daily_sources, fetched_at = \
            set_fetched_at(daily_campaigns, daily_sources, date)

        with app.test_request_context():
            db.init_app(app)
            save_data_to_db(daily_campaigns, daily_sources)

        print(daily_campaigns)
        print(daily_sources)
        time.sleep(7)


if __name__ == '__main__':
    config = read_config()
    api = ApiUtils(config)
    init_logger()

    schedule.every(1).minutes.do(live_job)
    schedule.every().day.at("04:00").do(daily_job)

    logging.info('Run data gathering script')
    live_job()
    while 1:
        schedule.run_pending()
        time.sleep(1)
