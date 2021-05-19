from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import synonym

db = SQLAlchemy(session_options={
    'expire_on_commit': False
})


class Campaign(db.Model):
    campaign_id = Column(Integer, primary_key=True)
    name = Column(String)
    traffic_source = Column(String)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    fetched_at = Column(DateTime)
    fetched_time = synonym('fetched_at')

    def __init__(self, name, revenue, traffic_source):
        self.name = name
        self.revenue = revenue
        self.traffic_source = traffic_source

    def __repr__(self):
        return f"Campaign (name={self.name}, traffic source={self.traffic_source}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" fetched_at={self.fetched_at})"

    def cast_to_daily(self):
        daily = DailyCampaign(self.name, self.revenue, self.traffic_source)
        daily.cost = self.cost
        daily.profit = self.profit
        daily.fetched_at = self.fetched_at
        return daily


class DailyCampaign(db.Model):
    campaign_id = Column(Integer, primary_key=True)
    name = Column(String)
    traffic_source = Column(String)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    fetched_at = Column(DateTime)

    def __init__(self, name, revenue, traffic_source):
        self.name = name
        self.revenue = revenue
        self.traffic_source = traffic_source

    def __repr__(self):
        return f"DailyCampaign (name={self.name}, traffic source={self.traffic_source}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" fetched_at={self.fetched_at})"


class Source(db.Model):
    source_id = Column(Integer, primary_key=True)
    name = Column(String)
    campaign_name = Column(String)
    traffic_source = Column(String)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    fetched_at = Column(DateTime)
    fetched_time = synonym('fetched_at')

    def __init__(self, name, campaign_name, revenue, traffic_source):
        self.name = name
        self.campaign_name = campaign_name
        self.revenue = revenue
        self.traffic_source = traffic_source

    def __repr__(self):
        return f"Source (name={self.name}, traffic source={self.traffic_source}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" campaign_name={self.campaign_name}, fetched_at={self.fetched_at})"

    def cast_to_daily(self):
        daily = DailySource(self.name, self.campaign_name, self.revenue, self.traffic_source)
        daily.cost = self.cost
        daily.profit = self.profit
        daily.fetched_at = self.fetched_at
        return daily


class DailySource(db.Model):
    source_id = Column(Integer, primary_key=True)
    name = Column(String)
    campaign_name = Column(String)
    traffic_source = Column(String)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    fetched_at = Column(DateTime)

    def __init__(self, name, campaign_name, revenue, traffic_source):
        self.name = name
        self.campaign_name = campaign_name
        self.revenue = revenue
        self.traffic_source = traffic_source

    def __repr__(self):
        return f"DailySource (name={self.name}, traffic source={self.traffic_source}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" campaign_name={self.campaign_name}, fetched_at={self.fetched_at})"


class CampaignRule(db.Model):
    rule_id = Column(Integer, primary_key=True)
    conditions = Column(Integer)
    campaign_name = Column(String)
    param1 = Column(String)
    sign1 = Column(String)
    value1 = Column(Float)
    param2 = Column(String)
    sign2 = Column(String)
    value2 = Column(Float)
    param3 = Column(String)
    sign3 = Column(String)
    value3 = Column(Float)
    param4 = Column(String)
    sign4 = Column(String)
    value4 = Column(Float)
    days = Column(Integer)
    action = Column(String)

    def __repr__(self):
        return f"CampaignRule (id={self.rule_id})"


class SourceRule(db.Model):
    rule_id = Column(Integer, primary_key=True)
    conditions = Column(Integer)
    source_name = Column(String)
    campaign_name = Column(String)
    param1 = Column(String)
    sign1 = Column(String)
    value1 = Column(Float)
    param2 = Column(String)
    sign2 = Column(String)
    value2 = Column(Float)
    param3 = Column(String)
    sign3 = Column(String)
    value3 = Column(Float)
    param4 = Column(String)
    sign4 = Column(String)
    value4 = Column(Float)
    days = Column(Integer)
    action = Column(String)

    def __repr__(self):
        return f"SourceRule (id={self.rule_id})"
