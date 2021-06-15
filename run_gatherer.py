import logging
import time
from datetime import datetime, timedelta

import schedule as schedule

from gatherer.utils import set_fetched_at, get_last_fetched, save_data_to_db, remove_data_fetched_at, set_last_fetched, \
    campaigns_to_daily, sources_to_daily, remove_daily_data
from models.models import db, DailyCampaign, DailySource, Binom, TrafficSource
from run_web import app
from utils.api_utils import ApiUtils
from utils.utils import read_config, init_logger, init_file_logger

api = None
config = None


def live_job():
    with app.test_request_context():
        db.init_app(app)

        now = datetime.now()
        fetched_campaigns = []
        fetched_sources = []

        binoms = Binom.query.all()
        for binom in binoms:
            ts_list = TrafficSource.query.filter_by(binom_id=binom.id).all()
            for ts in ts_list:
                if ts.credentials_id != -1:
                    campaigns = api.get_campaigns(ts, binom)
                    sources = api.get_sources(campaigns, ts, binom)
                    campaigns, sources, fetched_at = set_fetched_at(campaigns, sources, now)
                    fetched_campaigns += campaigns
                    fetched_sources += sources
                    logging.debug(f"Campaigns ({binom.name}, {ts.binom_ts_id}):\n{campaigns}")
                    logging.debug(f"Sources({binom.name}, {ts.binom_ts_id}):\n{sources}")

        last_fetched_at = get_last_fetched()
        remove_data_fetched_at(last_fetched_at)
        save_data_to_db(fetched_campaigns, fetched_sources)
        set_last_fetched(fetched_at)


def check_rules_job():
    with app.test_request_context():
        db.init_app(app)
        api.check_campaign_rules()
        api.check_source_rules()


def daily_job():
    now = datetime.now()
    yesterday = datetime(now.year, now.month, now.day, 0, 0, 0) - timedelta(1)
    fetched_campaigns = []
    fetched_sources = []

    with app.test_request_context():
        db.init_app(app)

        binoms = Binom.query.all()
        for binom in binoms:
            ts_list = TrafficSource.query.filter_by(binom_id=binom.id).all()
            for ts in ts_list:
                if ts.credentials_id != -1:
                    campaigns = api.get_campaigns(ts, binom, start_date=yesterday, end_date=yesterday)
                    sources = api.get_sources(campaigns, ts, binom, start_date=yesterday, end_date=yesterday)

                    daily_campaigns = campaigns_to_daily(campaigns)
                    daily_sources = sources_to_daily(sources)

                    fetched_campaigns += daily_campaigns
                    fetched_sources += daily_sources

                    daily_campaigns, daily_sources, fetched_at = set_fetched_at(daily_campaigns, daily_sources, yesterday)

        save_data_to_db(daily_campaigns, daily_sources)
        last_day = yesterday - timedelta(30)
        DailyCampaign.query.filter_by(fetched_at=last_day).delete()
        DailySource.query.filter_by(fetched_at=last_day).delete()
        db.session.commit()


def extract_n_days_job(ts, binom, days):
    for days in range(1, days):
        date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days)

        with app.test_request_context():
            db.init_app(app)
            logging.debug(f'Extracting campaigns for {date}')
            campaigns = api.get_campaigns(ts, binom, date, date)

            logging.debug(f'Extracting sources for {date}')
            sources = api.get_sources(campaigns, ts, binom, date, date)

            daily_campaigns = campaigns_to_daily(campaigns)
            daily_sources = sources_to_daily(sources)

            daily_campaigns, daily_sources, fetched_at = \
                set_fetched_at(daily_campaigns, daily_sources, date)

            save_data_to_db(daily_campaigns, daily_sources)

        logging.debug(daily_campaigns)
        logging.debug(daily_sources)
        time.sleep(3)


if __name__ == '__main__':
    config = read_config()
    api = ApiUtils(config)
    init_logger()
    init_file_logger()

    # with app.test_request_context():
    #     db.init_app(app)
    ##     remove_daily_data()
    #
    #     binoms = Binom.query.all()
    #     for binom in binoms:
    #         ts_list = TrafficSource.query.filter_by(binom_id=binom.id).all()
    #         for ts in ts_list:
    #             extract_n_days_job(ts, binom, 30)

    schedule.every(2).minutes.do(live_job)
    schedule.every(5).minutes.do(check_rules_job)
    schedule.every().day.at("04:00").do(daily_job)

    logging.debug('Run data gathering script')
    live_job()
    check_rules_job()
    while 1:
        schedule.run_pending()
        time.sleep(1)
