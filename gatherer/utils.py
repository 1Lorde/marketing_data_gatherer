from datetime import datetime

from models.models import db, Campaign, Source, ExtractedSource, ExtractedCampaign


def set_fetched_at(campaigns, sources, fetched_at=None):
    if not fetched_at:
        fetched_at = datetime.now()

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
    db.session.flush()
    db.session.add_all(campaigns)
    db.session.add_all(sources)
    db.session.commit()


def remove_data_fetched_at(fetched_at):
    Campaign.query.filter_by(fetched_at=fetched_at).delete()
    Source.query.filter_by(fetched_at=fetched_at).delete()
    db.session.commit()


def remove_extracted_data():
    ExtractedCampaign.query.delete()
    ExtractedSource.query.delete()
    db.session.commit()


def campaigns_to_extracted(campaigns, last_days=None):
    extracted = []
    for campaign in campaigns:
        extracted_campaign = campaign.cast_to_extracted()
        if last_days:
            extracted_campaign.last_days = last_days

        extracted.append(extracted_campaign)

    return extracted


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
