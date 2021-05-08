from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import synonym

db = SQLAlchemy()


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


class TrafficSource(db.Model):
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
        return f"TrafficSource (name={self.name}, revenue={self.revenue}, cost={self.cost}, profit={self.profit}," \
               f" campaign_name={self.campaign_name}, fetched_at={self.fetched_at})"
