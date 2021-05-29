import logging
import time
from datetime import datetime, timedelta

import schedule as schedule

from gatherer.utils import set_fetched_at, get_last_fetched, save_data_to_db, remove_data_fetched_at, set_last_fetched, \
    campaigns_to_daily, sources_to_daily
from models.models import db, DailyCampaign, DailySource
from run_web import app
from utils.api_utils import ApiUtils
from utils.utils import read_config, init_logger, init_file_logger

api = None
config = None


def live_job():
    ph_id = config['traffic_source_ids']['push_house']
    ungads_id = config['traffic_source_ids']['ungads']

    ph_campaigns = api.get_campaigns(ph_id)
    ph_sources = api.get_sources(ph_campaigns, ph_id)

    ungads_campaigns = api.get_campaigns(ungads_id)
    ungads_sources = api.get_sources(ungads_campaigns, ungads_id)

    now = datetime.now()
    ph_campaigns, ph_sources, fetched_at = set_fetched_at(ph_campaigns, ph_sources, now)
    ungads_campaigns, ungads_sources, fetched_at = set_fetched_at(ungads_campaigns, ungads_sources, now)

    last_fetched_at = get_last_fetched()

    with app.test_request_context():
        db.init_app(app)

        remove_data_fetched_at(last_fetched_at)
        save_data_to_db(ph_campaigns, ph_sources)
        save_data_to_db(ungads_campaigns, ungads_sources)
        set_last_fetched(fetched_at)

        logging.debug(ph_campaigns)
        logging.debug(ph_sources)
        logging.debug(ungads_campaigns)
        logging.debug(ungads_sources)


def check_rules_job():
    with app.test_request_context():
        api.check_campaign_rules()
        api.check_source_rules()


def daily_job():
    ph_id = config['traffic_source_ids']['push_house']
    ungads_id = config['traffic_source_ids']['ungads']

    now = datetime.now()
    yesterday = datetime(now.year, now.month, now.day, 0, 0, 0) - timedelta(1)

    ph_campaigns = api.get_campaigns(ph_id, start_date=yesterday, end_date=yesterday)
    ph_sources = api.get_sources(ph_campaigns, ph_id, start_date=yesterday, end_date=yesterday)

    ungads_campaigns = api.get_campaigns(ungads_id, start_date=yesterday, end_date=yesterday)
    ungads_sources = api.get_sources(ungads_campaigns, ungads_id, start_date=yesterday, end_date=yesterday)

    with app.test_request_context():
        db.init_app(app)
        daily_ph_campaigns = campaigns_to_daily(ph_campaigns)
        daily_ph_sources = sources_to_daily(ph_sources)

        daily_ungads_campaigns = campaigns_to_daily(ungads_campaigns)
        daily_ungads_sources = sources_to_daily(ungads_sources)

        daily_ph_campaigns, daily_ph_sources, fetched_at = \
            set_fetched_at(daily_ph_campaigns, daily_ph_sources, yesterday)

        daily_ungads_campaigns, daily_ungads_sources, fetched_at = \
            set_fetched_at(daily_ungads_campaigns, daily_ungads_sources, yesterday)

        save_data_to_db(daily_ph_campaigns, daily_ph_sources)
        save_data_to_db(daily_ungads_campaigns, daily_ungads_sources)

        last_day = yesterday - timedelta(30)
        DailyCampaign.query.filter_by(fetched_at=last_day).delete()
        DailySource.query.filter_by(fetched_at=last_day).delete()
        db.session.commit()


def extract_n_days_job(ts_id, days):
    # with app.test_request_context():
    #     db.init_app(app)
    #     remove_daily_data()

    for days in range(1, days):
        date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days)

        logging.debug(f'Extracting campaigns for {date}')
        campaigns = api.get_campaigns(ts_id, date, date)

        logging.debug(f'Extracting sources for {date}')
        sources = api.get_sources(campaigns, ts_id, date, date)

        daily_campaigns = campaigns_to_daily(campaigns)
        daily_sources = sources_to_daily(sources)

        daily_campaigns, daily_sources, fetched_at = \
            set_fetched_at(daily_campaigns, daily_sources, date)

        with app.test_request_context():
            db.init_app(app)
            save_data_to_db(daily_campaigns, daily_sources)

        logging.debug(daily_campaigns)
        logging.debug(daily_sources)
        time.sleep(7)


if __name__ == '__main__':
    config = read_config()
    api = ApiUtils(config)
    init_logger()
    init_file_logger()

    schedule.every(1).minutes.do(live_job)
    schedule.every(3).minutes.do(check_rules_job)
    schedule.every().day.at("04:00").do(daily_job)

    logging.debug('Run data gathering script')
    live_job()
    check_rules_job()
    while 1:
        schedule.run_pending()
        time.sleep(1)
