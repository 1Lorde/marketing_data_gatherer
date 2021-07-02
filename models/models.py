from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import synonym

db = SQLAlchemy(session_options={
    'expire_on_commit': False
})


class Campaign(db.Model):
    campaign_id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    traffic_source = Column(String)
    binom_source = Column(String)
    clicks = Column(Integer)
    binom_clicks = Column(Integer)
    impressions = Column(Integer)
    lp_clicks = Column(Integer)
    ctr = Column(Float)
    lp_ctr = Column(Float)
    leads = Column(Integer)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    roi = Column(Float)
    payout = Column(Float)
    cpc = Column(Float)
    cpm = Column(Float)
    epc = Column(Float)
    status = Column(String)
    fetched_at = Column(DateTime)
    fetched_time = synonym('fetched_at')

    def __init__(self, name, revenue, traffic_source):
        self.name = name
        self.traffic_source = traffic_source
        self.binom_source = 'undefined'
        self.clicks = 0
        self.binom_clicks = 0
        self.impressions = 0
        self.lp_clicks = 0
        self.ctr = 0
        self.lp_ctr = 0
        self.leads = 0
        self.cost = 0
        self.profit = 0
        self.roi = 0
        self.payout = 0
        self.cpc = 0
        self.cpm = 0
        self.epc = 0
        self.revenue = revenue
        self.cost = 0
        self.profit = 0
        self.status = 'undefined'

    def __repr__(self):
        return f"Campaign (name={self.name}, traffic source={self.traffic_source}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" fetched_at={self.fetched_at})"

    def cast_to_daily(self):
        daily = DailyCampaign(self.name, self.revenue, self.traffic_source)
        daily.binom_source = self.binom_source
        daily.clicks = self.clicks
        daily.binom_clicks = self.binom_clicks
        daily.impressions = self.impressions
        daily.lp_clicks = self.lp_clicks
        daily.ctr = self.ctr
        daily.lp_ctr = self.lp_ctr
        daily.leads = self.leads
        daily.cost = self.cost
        daily.profit = self.profit
        daily.roi = self.roi
        daily.payout = self.payout
        daily.cpc = self.cpc
        daily.cpm = self.cpm
        daily.epc = self.epc
        daily.cost = self.cost
        daily.profit = self.profit
        return daily


class DailyCampaign(db.Model):
    campaign_id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    traffic_source = Column(String)
    binom_source = Column(String)
    clicks = Column(Integer)
    binom_clicks = Column(Integer)
    impressions = Column(Integer)
    lp_clicks = Column(Integer)
    ctr = Column(Float)
    lp_ctr = Column(Float)
    leads = Column(Integer)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    roi = Column(Float)
    payout = Column(Float)
    cpc = Column(Float)
    cpm = Column(Float)
    epc = Column(Float)
    fetched_at = Column(DateTime)

    def __init__(self, name, revenue, traffic_source):
        self.name = name
        self.traffic_source = traffic_source
        self.binom_source = 'bin.mapletrack.com'
        self.clicks = 0
        self.binom_clicks = 0
        self.impressions = 0
        self.lp_clicks = 0
        self.ctr = 0
        self.lp_ctr = 0
        self.leads = 0
        self.cost = 0
        self.profit = 0
        self.roi = 0
        self.payout = 0
        self.cpc = 0
        self.cpm = 0
        self.epc = 0
        self.revenue = revenue
        self.cost = 0
        self.profit = 0

    def __repr__(self):
        return f"DailyCampaign (name={self.name}, traffic source={self.traffic_source}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" fetched_at={self.fetched_at})"


class Source(db.Model):
    source_id = Column(Integer, primary_key=True)
    name = Column(String)
    campaign_name = Column(String)
    description = Column(String)
    traffic_source = Column(String)
    binom_source = Column(String)
    clicks = Column(Integer)
    binom_clicks = Column(Integer)
    impressions = Column(Integer)
    lp_clicks = Column(Integer)
    ctr = Column(Float)
    lp_ctr = Column(Float)
    leads = Column(Integer)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    roi = Column(Float)
    payout = Column(Float)
    cpc = Column(Float)
    cpm = Column(Float)
    epc = Column(Float)
    status = Column(String)
    fetched_at = Column(DateTime)
    fetched_time = synonym('fetched_at')

    def __init__(self, name, campaign_name, revenue, traffic_source):
        self.name = name
        self.campaign_name = campaign_name
        self.traffic_source = traffic_source
        self.binom_source = 'undefined'
        self.clicks = 0
        self.binom_clicks = 0
        self.impressions = 0
        self.lp_clicks = 0
        self.ctr = 0
        self.lp_ctr = 0
        self.leads = 0
        self.cost = 0
        self.profit = 0
        self.roi = 0
        self.payout = 0
        self.cpc = 0
        self.cpm = 0
        self.epc = 0
        self.revenue = revenue
        self.cost = 0
        self.profit = 0
        self.status = 'undefined'

    def __repr__(self):
        return f"Source (name={self.name}, traffic source={self.traffic_source}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" campaign_name={self.campaign_name}, fetched_at={self.fetched_at})"

    def cast_to_daily(self):
        daily = DailySource(self.name, self.campaign_name, self.revenue, self.traffic_source)
        daily.binom_source = self.binom_source
        daily.clicks = self.clicks
        daily.binom_clicks = self.binom_clicks
        daily.impressions = self.impressions
        daily.lp_clicks = self.lp_clicks
        daily.ctr = self.ctr
        daily.lp_ctr = self.lp_ctr
        daily.leads = self.leads
        daily.cost = self.cost
        daily.profit = self.profit
        daily.roi = self.roi
        daily.payout = self.payout
        daily.cpc = self.cpc
        daily.cpm = self.cpm
        daily.epc = self.epc
        daily.cost = self.cost
        daily.profit = self.profit
        return daily


class DailySource(db.Model):
    source_id = Column(Integer, primary_key=True)
    name = Column(String)
    campaign_name = Column(String)
    description = Column(String)
    traffic_source = Column(String)
    binom_source = Column(String)
    clicks = Column(Integer)
    binom_clicks = Column(Integer)
    impressions = Column(Integer)
    lp_clicks = Column(Integer)
    ctr = Column(Float)
    lp_ctr = Column(Float)
    leads = Column(Integer)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    roi = Column(Float)
    payout = Column(Float)
    cpc = Column(Float)
    cpm = Column(Float)
    epc = Column(Float)
    fetched_at = Column(DateTime)

    def __init__(self, name, campaign_name, revenue, traffic_source):
        self.name = name
        self.campaign_name = campaign_name
        self.traffic_source = traffic_source
        self.binom_source = 'bin.mapletrack.com'
        self.clicks = 0
        self.binom_clicks = 0
        self.impressions = 0
        self.lp_clicks = 0
        self.ctr = 0
        self.lp_ctr = 0
        self.leads = 0
        self.cost = 0
        self.profit = 0
        self.roi = 0
        self.payout = 0
        self.cpc = 0
        self.cpm = 0
        self.epc = 0
        self.revenue = revenue
        self.cost = 0
        self.profit = 0

    def __repr__(self):
        return f"DailySource (name={self.name}, traffic source={self.traffic_source}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" campaign_name={self.campaign_name}, fetched_at={self.fetched_at})"


class CampaignRule(db.Model):
    rule_id = Column(Integer, primary_key=True)
    conditions = Column(Integer)
    campaign_name = Column(String)

    ts_id = db.Column(db.Integer, db.ForeignKey('traffic_source.id'), nullable=False)
    ts = db.relationship('TrafficSource', backref=db.backref('templates', lazy=True))

    param1 = Column(String)
    sign1 = Column(String)
    value1 = Column(Float)
    factor1 = Column(Float)
    factor_var1 = Column(String)
    param2 = Column(String)
    sign2 = Column(String)
    value2 = Column(Float)
    factor2 = Column(Float)
    factor_var2 = Column(String)
    param3 = Column(String)
    sign3 = Column(String)
    value3 = Column(Float)
    factor3 = Column(Float)
    factor_var3 = Column(String)
    param4 = Column(String)
    sign4 = Column(String)
    value4 = Column(Float)
    factor4 = Column(Float)
    factor_var4 = Column(String)
    days = Column(Integer)
    action = Column(String)

    def __repr__(self):
        return f"CampaignRule (id={self.rule_id})"


class SourceRule(db.Model):
    rule_id = Column(Integer, primary_key=True)
    conditions = Column(Integer)
    source_name = Column(String)
    campaign_name = Column(String)

    ts_id = db.Column(db.Integer, db.ForeignKey('traffic_source.id'), nullable=False)
    ts = db.relationship('TrafficSource', backref=db.backref('templates1', lazy=True))

    param1 = Column(String)
    sign1 = Column(String)
    value1 = Column(Float)
    factor1 = Column(Float)
    factor_var1 = Column(String)
    param2 = Column(String)
    sign2 = Column(String)
    value2 = Column(Float)
    factor2 = Column(Float)
    factor_var2 = Column(String)
    param3 = Column(String)
    sign3 = Column(String)
    value3 = Column(Float)
    factor3 = Column(Float)
    factor_var3 = Column(String)
    param4 = Column(String)
    sign4 = Column(String)
    value4 = Column(Float)
    factor4 = Column(Float)
    factor_var4 = Column(String)
    days = Column(Integer)
    action = Column(String)

    def __repr__(self):
        return f"SourceRule (id={self.rule_id})"


class TrafficSource(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    binom_ts_id = Column(String)

    binom_id = db.Column(db.Integer, db.ForeignKey('binom.id'), nullable=False)
    binom = db.relationship('Binom', backref=db.backref('templates', lazy=True))

    credentials_id = db.Column(db.Integer, db.ForeignKey('traffic_source_credentials.id'), nullable=False)
    credentials = db.relationship('TrafficSourceCredentials', backref=db.backref('templates', lazy=True))

    def __init__(self, name, binom_ts_id, binom_id, credentials_id):
        self.name = name
        self.binom_ts_id = binom_ts_id
        self.binom_id = binom_id
        self.credentials_id = credentials_id

    def __repr__(self):
        return f"TrafficSource (name={self.name}, url={self.url}, binom_ts_id={self.binom_ts_id}, binom={self.binom.name})"


class PausedSource(db.Model):
    id = Column(Integer, primary_key=True)
    source_name = Column(String)
    campaign_name = Column(String)

    ts_id = db.Column(db.Integer, db.ForeignKey('traffic_source.id'), nullable=False)
    ts = db.relationship('TrafficSource', backref=db.backref('templates3', lazy=True))

    def __init__(self, source_name, campaign_name, ts: TrafficSource):
        self.source_name = source_name
        self.campaign_name = campaign_name
        self.ts = ts

    def __repr__(self):
        return f"PausedSource (source_name={self.source_name}, traffic source={self.ts_id}, campaign_name={self.campaign_name})"


class PausedCampaign(db.Model):
    id = Column(Integer, primary_key=True)
    campaign_name = Column(String)

    ts_id = db.Column(db.Integer, db.ForeignKey('traffic_source.id'), nullable=False)
    ts = db.relationship('TrafficSource', backref=db.backref('templates2', lazy=True))

    def __init__(self, campaign_name, ts: TrafficSource):
        self.campaign_name = campaign_name
        self.ts = ts

    def __repr__(self):
        return f"PausedCampaign (campaign_name={self.campaign_name}, traffic source={self.ts_id})"


class Binom(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    api_key = Column(String)

    def __init__(self, name, url, api_key):
        self.name = name
        self.url = url
        self.api_key = api_key

    def __repr__(self):
        return f"Binom (name={self.name}, url={self.url})"


class TrafficSourceCredentials(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    api_key = Column(String)

    def __init__(self, name, url, api_key):
        self.name = name
        self.url = url
        self.api_key = api_key

    def __repr__(self):
        return f"TrafficSourceCredentials (name={self.name}, url={self.url}, api_key={self.api_key})"


class SourcePrecalculatedStat(db.Model):
    source_id = Column(Integer, primary_key=True)
    name = Column(String)
    campaign_name = Column(String)
    description = Column(String)
    traffic_source = Column(String)
    binom_source = Column(String)
    clicks = Column(Integer)
    binom_clicks = Column(Integer)
    impressions = Column(Integer)
    lp_clicks = Column(Integer)
    ctr = Column(Float)
    lp_ctr = Column(Float)
    leads = Column(Integer)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    roi = Column(Float)
    payout = Column(Float)
    cpc = Column(Float)
    cpm = Column(Float)
    epc = Column(Float)
    status = Column(String)
    period_start = Column(DateTime)
    period_end = Column(DateTime)

    def __init__(self, name, campaign_name, revenue, traffic_source):
        self.name = name
        self.campaign_name = campaign_name
        self.traffic_source = traffic_source
        self.binom_source = 'undefined'
        self.clicks = 0
        self.binom_clicks = 0
        self.impressions = 0
        self.lp_clicks = 0
        self.ctr = 0
        self.lp_ctr = 0
        self.leads = 0
        self.cost = 0
        self.profit = 0
        self.roi = 0
        self.payout = 0
        self.cpc = 0
        self.cpm = 0
        self.epc = 0
        self.revenue = revenue
        self.cost = 0
        self.profit = 0
        self.status = 'undefined'

    def __repr__(self):
        return f"SourcePrecalculatedStat (name={self.name}, traffic source={self.traffic_source}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" campaign_name={self.campaign_name}, period_start={self.period_start}, period_end={self.period_end})"
