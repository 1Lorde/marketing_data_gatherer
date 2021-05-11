from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import synonym

db = SQLAlchemy(session_options={
    'expire_on_commit': False
})


class Campaign(db.Model):
    campaign_id = Column(Integer, primary_key=True)
    name = Column(String)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    fetched_at = Column(DateTime)
    fetched_time = synonym('fetched_at')

    def __init__(self, name, revenue):
        self.name = name
        self.revenue = revenue

    def __repr__(self):
        return f"Campaign (name={self.name}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" fetched_at={self.fetched_at})"

    def cast_to_daily(self):
        daily = DailyCampaign(self.name, self.revenue)
        daily.cost = self.cost
        daily.profit = self.profit
        daily.fetched_at = self.fetched_at
        return daily

    def cast_to_extracted(self):
        extracted = ExtractedCampaign(self.name, self.revenue)
        extracted.cost = self.cost
        extracted.profit = self.profit
        extracted.fetched_at = self.fetched_at
        return extracted


class DailyCampaign(db.Model):
    campaign_id = Column(Integer, primary_key=True)
    name = Column(String)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    fetched_at = Column(DateTime)

    def __init__(self, name, revenue):
        self.name = name
        self.revenue = revenue

    def __repr__(self):
        return f"DailyCampaign (name={self.name}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" fetched_at={self.fetched_at})"


class ExtractedCampaign(db.Model):
    campaign_id = Column(Integer, primary_key=True)
    name = Column(String)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    last_days = Column(Integer)
    fetched_at = Column(DateTime)

    def __init__(self, name, revenue):
        self.name = name
        self.revenue = revenue

    def __repr__(self):
        return f"ExtractedCampaign (name={self.name}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" fetched_at={self.fetched_at})"


class Source(db.Model):
    source_id = Column(Integer, primary_key=True)
    name = Column(String)
    campaign_name = Column(String)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    fetched_at = Column(DateTime)
    fetched_time = synonym('fetched_at')

    def __init__(self, name, campaign_name, revenue):
        self.name = name
        self.campaign_name = campaign_name
        self.revenue = revenue

    def __repr__(self):
        return f"Source (name={self.name}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" campaign_name={self.campaign_name}, fetched_at={self.fetched_at})"

    def cast_to_daily(self):
        daily = DailySource(self.name, self.campaign_name, self.revenue)
        daily.cost = self.cost
        daily.profit = self.profit
        daily.fetched_at = self.fetched_at
        return daily

    def cast_to_extracted(self):
        extracted = ExtractedSource(self.name, self.campaign_name, self.revenue)
        extracted.cost = self.cost
        extracted.profit = self.profit
        extracted.fetched_at = self.fetched_at
        return extracted


class DailySource(db.Model):
    source_id = Column(Integer, primary_key=True)
    name = Column(String)
    campaign_name = Column(String)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    fetched_at = Column(DateTime)

    def __init__(self, name, campaign_name, revenue):
        self.name = name
        self.campaign_name = campaign_name
        self.revenue = revenue

    def __repr__(self):
        return f"DailySource (name={self.name}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" campaign_name={self.campaign_name}, fetched_at={self.fetched_at})"


class ExtractedSource(db.Model):
    source_id = Column(Integer, primary_key=True)
    name = Column(String)
    campaign_name = Column(String)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    last_days = Column(Integer)
    fetched_at = Column(DateTime)

    def __init__(self, name, campaign_name, revenue):
        self.name = name
        self.campaign_name = campaign_name
        self.revenue = revenue

    def __repr__(self):
        return f"ExtractedSource (name={self.name}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" campaign_name={self.campaign_name}, fetched_at={self.fetched_at})"
