from flask_table import Table, Col, DatetimeCol


class CampaignTable(Table):
    classes = ['table', 'is-striped', 'is-hoverable', 'is-fullwidth', 'is-bordered']
    fetched_time = DatetimeCol("Time", datetime_format="HH:mm:ss")
    fetched_at = DatetimeCol("Date", datetime_format="dd-MM-yy")
    name = Col("Campaign name")
    revenue = Col("Revenue")
    cost = Col("Cost")
    profit = Col("Profit")

    def get_thead_attrs(self):
        return {'style': 'position: sticky; top: 0; '}


class TrafficSourceTable(Table):
    classes = ['table', 'is-striped', 'is-hoverable', 'is-fullwidth', 'is-bordered']
    fetched_time = DatetimeCol("Time", datetime_format="HH:mm:ss")
    fetched_at = DatetimeCol("Date", datetime_format="dd-MM-yy")
    name = Col("Source name")
    campaign_name = Col("Campaign name")
    revenue = Col("Revenue")
    cost = Col("Cost")
    profit = Col("Profit")

    def get_thead_attrs(self):
        return {'style': 'position: sticky; top: 0; '}