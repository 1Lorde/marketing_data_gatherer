from flask_table import Table, Col, DatetimeCol


class Col(Col):
    def td_format(self, content):
        if isinstance(content, float):
            return "%.5f" % content
        return content


class NameCol(Col):
    def td_format(self, content):
        return '<strong><i>' + content + '</i></strong>'


class StatusCol(Col):
    def td_format(self, content):
        if content == 'running':
            return '<span class="tag is-small is-light is-info">' + content + '</span>'

        return '<span class="tag is-small is-light is-dark">' + content + '</span>'


class TrafficSourceCol(Col):
    def td_format(self, content):
        if content == '29':
            return '<span>Push.House</span>'
        elif content == '33':
            return '<span>Ungads</span>'
        else:
            return '<span>' + content + '</span>'


class RoiCol(Col):
    def td_format(self, content):
        if content < 0:
            return '<span class="has-text-danger">' + str("%.0f" % content) + '%' + '</span>'
        else:
            return '<span class="has-text-success">' + str("%.0f" % content) + '%' + '</span>'


class CtrCol(Col):
    def td_format(self, content):
        return '<span>' + str("%.2f" % content) + '%' + '</span>'


class CampaignTable(Table):
    classes = ['table', 'is-striped', 'is-hoverable', 'is-fullwidth', 'is-bordered', 'is-size-7']
    fetched_time = DatetimeCol("Updated at", datetime_format="HH:mm:ss")
    name = NameCol("Campaign name")
    traffic_source = TrafficSourceCol("Traffic source")
    binom_source = Col("Binom source")
    clicks = Col("Clicks")
    binom_clicks = Col("Binom clicks")
    impressions = Col("Impressions")
    lp_clicks = Col("LP clicks")
    ctr = CtrCol("CTR")
    lp_ctr = CtrCol("LP CTR")
    leads = Col("Leads")
    cost = Col("Cost")
    revenue = Col("Revenue")
    profit = Col("Profit")
    roi = RoiCol("ROI")
    payout = Col("Payout")
    cpc = Col("CPC")
    cpm = Col("CPM")
    epc = Col("EPC")
    status = StatusCol("Status")

    def get_thead_attrs(self):
        return {'style': 'position: sticky; top: 0; '}


class DailyCampaignTable(Table):
    classes = ['table', 'is-striped', 'is-hoverable', 'is-fullwidth', 'is-bordered', 'is-size-7']
    fetched_at = DatetimeCol("Date", datetime_format="dd-MM-yy")
    name = NameCol("Campaign name")
    traffic_source = TrafficSourceCol("Traffic source")
    binom_source = Col("Binom source")
    clicks = Col("Clicks")
    binom_clicks = Col("Binom clicks")
    impressions = Col("Impressions")
    lp_clicks = Col("LP clicks")
    ctr = CtrCol("CTR")
    lp_ctr = CtrCol("LP CTR")
    leads = Col("Leads")
    cost = Col("Cost")
    revenue = Col("Revenue")
    profit = Col("Profit")
    roi = RoiCol("ROI")
    payout = Col("Payout")
    cpc = Col("CPC")
    cpm = Col("CPM")
    epc = Col("EPC")

    def get_thead_attrs(self):
        return {'style': 'position: sticky; top: 0; '}


class CampaignStatsTable(Table):
    classes = ['table', 'is-striped', 'is-hoverable', 'is-fullwidth', 'is-bordered', 'is-size-7']
    name = NameCol("Campaign name")
    traffic_source = TrafficSourceCol("Traffic source")
    binom_source = Col("Binom source")
    clicks = Col("Clicks")
    binom_clicks = Col("Binom clicks")
    impressions = Col("Impressions")
    lp_clicks = Col("LP clicks")
    ctr = CtrCol("CTR")
    lp_ctr = CtrCol("LP CTR")
    leads = Col("Leads")
    cost = Col("Cost")
    revenue = Col("Revenue")
    profit = Col("Profit")
    roi = RoiCol("ROI")
    payout = Col("Payout")
    cpc = Col("CPC")
    cpm = Col("CPM")
    epc = Col("EPC")

    def get_thead_attrs(self):
        return {'style': 'position: sticky; top: 0; '}


class SourceTable(Table):
    classes = ['table', 'is-striped', 'is-hoverable', 'is-fullwidth', 'is-bordered', 'is-size-7']
    fetched_time = DatetimeCol("Updated at", datetime_format="HH:mm:ss")
    name = NameCol("Source name")
    campaign_name = Col("Campaign name")
    traffic_source = TrafficSourceCol("Traffic source")
    binom_source = Col("Binom source")
    clicks = Col("Clicks")
    binom_clicks = Col("Binom clicks")
    impressions = Col("Impressions")
    lp_clicks = Col("LP clicks")
    ctr = CtrCol("CTR")
    lp_ctr = CtrCol("LP CTR")
    leads = Col("Leads")
    cost = Col("Cost")
    revenue = Col("Revenue")
    profit = Col("Profit")
    roi = RoiCol("ROI")
    payout = Col("Payout")
    cpc = Col("CPC")
    cpm = Col("CPM")
    epc = Col("EPC")
    status = StatusCol("Status")

    def get_thead_attrs(self):
        return {'style': 'position: sticky; top: 0; '}


class DailySourceTable(Table):
    classes = ['table', 'is-striped', 'is-hoverable', 'is-fullwidth', 'is-bordered', 'is-size-7']
    fetched_at = DatetimeCol("Date", datetime_format="dd-MM-yy")
    name = NameCol("Source name")
    campaign_name = Col("Campaign name")
    traffic_source = TrafficSourceCol("Traffic source")
    binom_source = Col("Binom source")
    clicks = Col("Clicks")
    binom_clicks = Col("Binom clicks")
    impressions = Col("Impressions")
    lp_clicks = Col("LP clicks")
    ctr = CtrCol("CTR")
    lp_ctr = CtrCol("LP CTR")
    leads = Col("Leads")
    cost = Col("Cost")
    revenue = Col("Revenue")
    profit = Col("Profit")
    roi = RoiCol("ROI")
    payout = Col("Payout")
    cpc = Col("CPC")
    cpm = Col("CPM")
    epc = Col("EPC")

    def get_thead_attrs(self):
        return {'style': 'position: sticky; top: 0; '}


class SourceStatsTable(Table):
    classes = ['table', 'is-striped', 'is-hoverable', 'is-fullwidth', 'is-bordered', 'is-size-7']
    name = NameCol("Source name")
    campaign_name = Col("Campaign name")
    traffic_source = TrafficSourceCol("Traffic source")
    binom_source = Col("Binom source")
    clicks = Col("Clicks")
    binom_clicks = Col("Binom clicks")
    impressions = Col("Impressions")
    lp_clicks = Col("LP clicks")
    ctr = CtrCol("CTR")
    lp_ctr = CtrCol("LP CTR")
    leads = Col("Leads")
    cost = Col("Cost")
    revenue = Col("Revenue")
    profit = Col("Profit")
    roi = RoiCol("ROI")
    payout = Col("Payout")
    cpc = Col("CPC")
    cpm = Col("CPM")
    epc = Col("EPC")

    def get_thead_attrs(self):
        return {'style': 'position: sticky; top: 0; '}
