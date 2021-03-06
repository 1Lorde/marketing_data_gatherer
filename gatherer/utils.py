from datetime import datetime

from models.models import db, Campaign, Source, DailyCampaign, DailySource, TrafficSource


def set_fetched_at(campaigns, sources, fetched_at):
    for campaign in campaigns:
        campaign.fetched_at = fetched_at

    for source in sources:
        source.fetched_at = fetched_at

    return campaigns, sources, fetched_at


def set_last_fetched(fetched_at):
    with open('gatherer/last_fetched_at', 'w') as f:
        f.write(str(fetched_at))


def get_last_fetched():
    with open('gatherer/last_fetched_at', 'r') as f:
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


def remove_daily_data():
    DailyCampaign.query.delete()
    DailySource.query.delete()
    db.session.commit()


def campaigns_to_daily(campaigns):
    daily = []
    for campaign in campaigns:
        daily.append(campaign.cast_to_daily())

    return daily


def sources_to_extracted(sources, last_days=None):
    extracted = []
    for source in sources:
        extracted_source = source.cast_to_extracted()
        if last_days:
            extracted_source.last_days = last_days

        extracted.append(extracted_source)

    return extracted


def sources_to_daily(sources):
    daily = []
    for source in sources:
        daily.append(source.cast_to_daily())

    return daily


def is_push_house(ts: TrafficSource):
    if 'push.house' in ts.url:
        return True
    else:
        return False


def is_ungads(ts: TrafficSource):
    if 'ungads' in ts.url:
        return True
    else:
        return False