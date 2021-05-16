import datetime
import os
from datetime import timedelta

from flask import Flask, render_template, redirect, url_for, request
from sqlalchemy import and_
from sqlalchemy_utils import database_exists

from models.models import db, Campaign, Source, DailyCampaign, DailySource, \
    CampaignRule, SourceRule
from utils.api_utils import ApiUtils
from utils.rules_utils import set_campaign_rule_fields, save_rule_to_db, set_source_rule_fields
from utils.utils import read_config, init_logger
from web.service import paginate_data, get_pagination_metadata_from_query, get_path_args, render_empty_campaigns, \
    render_empty_sources, get_rule_fields
from web.tables import CampaignTable, SourceTable, SourceStatsTable, DailyCampaignTable, CampaignStatsTable, \
    DailySourceTable

template_dir = os.path.abspath('web/templates')

app = Flask(__name__, template_folder=template_dir)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
    if not os.path.exists('data'):
        os.mkdir('data')
    with app.test_request_context():
        db.init_app(app)
        db.create_all()

api = None


@app.context_processor
def inject_dates():
    return {'today': datetime.date.today(),
            'yesterday': datetime.date.today() - timedelta(days=1),
            'three_days': datetime.date.today() - timedelta(days=3),
            'week': datetime.date.today() - timedelta(days=7),
            }


@app.route('/campaigns/current', methods=['GET', 'POST'])
def current_campaigns():
    page_arg, start_arg, end_arg = get_path_args()
    campaign_query = Campaign.query.order_by(Campaign.name)

    today = str(datetime.datetime.today()).split(' ')[0]
    today_start = datetime.datetime.strptime(today + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    today_end = datetime.datetime.strptime(today + ' 23:59:59', '%Y-%m-%d %H:%M:%S')

    campaign_query = campaign_query.filter(
        and_(Campaign.fetched_at >= today_start,
             Campaign.fetched_at <= today_end))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, campaign_query)
    campaigns_list = paginate_data(pagination_metadata, campaign_query)

    if len(campaigns_list) == 0:
        return render_empty_campaigns('current_campaigns.html')

    table = CampaignTable(campaigns_list)

    return render_template('current_campaigns.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg)


@app.route('/campaigns/stats', methods=['GET', 'POST'])
def campaigns_stats():
    if request.method == 'POST':
        try:
            days_campaigns = request.form['days_campaigns'] if request.form['days_campaigns'] else None

            if days_campaigns:
                start = datetime.date.today() - timedelta(int(days_campaigns))
                end = datetime.date.today() - timedelta(1)
                return redirect(url_for('campaigns_stats', start=start, end=end))
        except KeyError:
            pass

    page_arg, start_arg, end_arg = get_path_args()

    yesterday = datetime.datetime.now() - timedelta(days=1)
    campaign_query = DailyCampaign.query.order_by(DailyCampaign.name)

    if start_arg and end_arg:
        start = start_arg + ' 00:00:00'
        end = end_arg + ' 23:59:59'
        campaign_query = campaign_query.filter(
            and_(DailyCampaign.fetched_at >= start,
                 DailyCampaign.fetched_at <= end))
    else:
        campaign_query = campaign_query.filter(
            and_(DailyCampaign.fetched_at >= yesterday - timedelta(1),
                 DailyCampaign.fetched_at <= yesterday))

    campaigns_list = campaign_query.all()

    unique_campaigns_names = set()
    [unique_campaigns_names.add(camp.name) for camp in campaigns_list if camp.name not in unique_campaigns_names]

    campaigns_stats_list = []
    for name in unique_campaigns_names:
        campaign_stat = Campaign(name, 0)
        campaign_stat.cost = 0
        campaign_stat.profit = 0

        for campaign in campaigns_list:
            if campaign.name == name:
                campaign_stat.revenue += campaign.revenue
                campaign_stat.cost += campaign.cost
                campaign_stat.profit += campaign.profit

        campaigns_stats_list.append(campaign_stat)

    if len(campaigns_stats_list) == 0:
        return render_empty_campaigns('campaigns_stats.html')

    campaigns_stats_list.sort(key=lambda x: x.name, reverse=True)

    table = CampaignStatsTable(campaigns_stats_list)

    return render_template('campaigns_stats.html',
                           table=table,
                           pagination_data=None,
                           start=start_arg,
                           end=end_arg)


@app.route('/campaigns/daily', methods=['GET', 'POST'])
def daily_campaigns():
    if request.method == 'POST':
        try:
            days_campaigns = request.form['days_campaigns'] if request.form['days_campaigns'] else None

            if days_campaigns:
                start = datetime.date.today() - timedelta(int(days_campaigns))
                end = start
                return redirect(url_for('daily_campaigns', start=start, end=end))
        except KeyError:
            pass

    page_arg, start_arg, end_arg = get_path_args()

    campaign_query = DailyCampaign.query.order_by(DailyCampaign.name)

    if start_arg and end_arg:
        start = start_arg + ' 00:00:00'
        end = end_arg + ' 23:59:59'
        campaign_query = campaign_query.filter(
            and_(DailyCampaign.fetched_at >= start,
                 DailyCampaign.fetched_at <= end))
    else:
        yesterday = datetime.datetime.now() - timedelta(days=1)

        campaign_query = campaign_query.filter(
            and_(DailyCampaign.fetched_at >= yesterday - timedelta(1),
                 DailyCampaign.fetched_at <= yesterday))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, campaign_query)
    campaigns_list = paginate_data(pagination_metadata, campaign_query)

    if len(campaigns_list) == 0:
        return render_empty_campaigns('daily_campaigns.html')

    table = DailyCampaignTable(campaigns_list)

    return render_template('daily_campaigns.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg)


@app.route('/sources/current', methods=['GET', 'POST'])
def current_sources():
    page_arg, start_arg, end_arg = get_path_args()
    source_query = Source.query.order_by(Source.campaign_name)

    today = str(datetime.datetime.today()).split(' ')[0]
    today_start = datetime.datetime.strptime(today + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    today_end = datetime.datetime.strptime(today + ' 23:59:59', '%Y-%m-%d %H:%M:%S')

    source_query = source_query.filter(
        and_(Source.fetched_at >= today_start,
             Source.fetched_at <= today_end))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, source_query)
    source_list = paginate_data(pagination_metadata, source_query)

    if len(source_list) == 0:
        return render_empty_sources('current_sources.html')

    table = SourceTable(source_list)

    return render_template('current_sources.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg)


@app.route('/sources/stats', methods=['GET', 'POST'])
def sources_stats():
    if request.method == 'POST':
        try:
            days_sources = request.form['days_sources'] if request.form['days_sources'] else None

            if days_sources:
                start = datetime.date.today() - timedelta(int(days_sources))
                end = datetime.date.today() - timedelta(1)
                return redirect(url_for('campaigns_stats', start=start, end=end))
        except KeyError:
            pass

    page_arg, start_arg, end_arg = get_path_args()

    yesterday = datetime.datetime.now() - timedelta(days=1)
    source_query = DailySource.query.order_by(DailySource.campaign_name)

    if start_arg and end_arg:
        start = start_arg + ' 00:00:00'
        end = end_arg + ' 23:59:59'
        source_query = source_query.filter(
            and_(DailySource.fetched_at >= start,
                 DailySource.fetched_at <= end))
    else:
        source_query = source_query.filter(
            and_(DailySource.fetched_at >= yesterday - timedelta(1),
                 DailySource.fetched_at <= yesterday))

    source_list = source_query.all()

    unique_sources_names = set()
    [unique_sources_names.add(source.name) for source in source_list if source.name not in unique_sources_names]

    unique_campaigns_names = set()
    [unique_campaigns_names.add(source.campaign_name) for source in source_list if
     source.campaign_name not in unique_campaigns_names]

    sources_stats_list = []
    for campaign_name in unique_campaigns_names:
        for name in unique_sources_names:
            source_stat = Source(name, campaign_name, 0)
            source_stat.cost = 0
            source_stat.profit = 0

            for source in source_list:
                if source.name == name and source.campaign_name == campaign_name:
                    source_stat.revenue += source.revenue
                    source_stat.cost += source.cost
                    source_stat.profit += source.profit

            sources_stats_list.append(source_stat)

    if len(sources_stats_list) == 0:
        return render_empty_sources('sources_stats.html')

    table = SourceStatsTable(sources_stats_list)

    return render_template('sources_stats.html',
                           table=table,
                           pagination_data=None,
                           start=start_arg,
                           end=end_arg)


@app.route('/sources/daily', methods=['GET', 'POST'])
def daily_sources():
    if request.method == 'POST':
        try:
            days_campaigns = request.form['days_sources'] if request.form['days_sources'] else None

            if days_campaigns:
                start = datetime.date.today() - timedelta(int(days_campaigns))
                end = start
                return redirect(url_for('daily_sources', start=start, end=end))
        except KeyError:
            pass

    page_arg, start_arg, end_arg = get_path_args()

    sources_query = DailySource.query.order_by(DailySource.campaign_name)

    if start_arg and end_arg:
        start = start_arg + ' 00:00:00'
        end = end_arg + ' 23:59:59'
        sources_query = sources_query.filter(
            and_(DailySource.fetched_at >= start,
                 DailySource.fetched_at <= end))
    else:
        yesterday = datetime.datetime.now() - timedelta(days=1)

        sources_query = sources_query.filter(
            and_(DailySource.fetched_at >= yesterday - timedelta(1),
                 DailySource.fetched_at <= yesterday))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, sources_query)
    sources_list = paginate_data(pagination_metadata, sources_query)

    if len(sources_list) == 0:
        return render_empty_sources('daily_sources.html')

    table = DailySourceTable(sources_list)

    return render_template('daily_sources.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg)


@app.route('/')
def root():
    return redirect(url_for('current_campaigns'))


@app.route('/campaigns/rules', methods=['GET', 'POST'])
def campaigns_rules():
    rules = CampaignRule.query.all()

    return render_template('campaigns_rules.html',
                           rules=rules)


@app.route('/sources/rules', methods=['GET', 'POST'])
def sources_rules():
    rules = SourceRule.query.all()
    return render_template('sources_rules.html',
                           rules=rules)


@app.route('/campaigns/rules/add', methods=['GET', 'POST'])
def campaigns_add_rule():
    if request.method == 'POST':
        rule_dict = get_rule_fields()
        print(rule_dict)
        rule = set_campaign_rule_fields(rule_dict)
        save_rule_to_db(rule)
        return redirect(url_for('campaigns_rules'))

    return render_template('add_campaign_rule.html',
                           form=None)


@app.route('/campaigns/rules/delete/<rule_id>', methods=['GET', 'POST'])
def campaigns_delete_rule(rule_id):
    deleted_rule = CampaignRule.query.filter_by(rule_id=rule_id).first()
    if request.method == 'POST':
        db.session.delete(deleted_rule)
        db.session.commit()
        return redirect(url_for('campaigns_rules'))

    return render_template('delete_confirm.html',
                           rule_id=deleted_rule,
                           message_title="Removing campaign rule",
                           message="Are you really want to delete rule for campaign " + deleted_rule.campaign_name + "?")


@app.route('/sources/rules/add', methods=['GET', 'POST'])
def sources_add_rule():
    if request.method == 'POST':
        rule_dict = get_rule_fields()
        print(rule_dict)
        rule = set_source_rule_fields(rule_dict)
        save_rule_to_db(rule)
        return redirect(url_for('sources_rules'))

    return render_template('add_source_rule.html',
                           form=None)


@app.route('/sources/rules/delete/<rule_id>', methods=['GET', 'POST'])
def sources_delete_rule(rule_id):
    deleted_rule = SourceRule.query.filter_by(rule_id=rule_id).first()
    if request.method == 'POST':
        db.session.delete(deleted_rule)
        db.session.commit()
        return redirect(url_for('sources_rules'))

    return render_template('delete_confirm.html',
                           rule_id=deleted_rule,
                           message_title="Removing SourceId rule",
                           message="Are you really want to delete rule for SourceId " + deleted_rule.source_name + "?")


if __name__ == '__main__':
    config = read_config()
    api = ApiUtils(config)
    init_logger()

    db.init_app(app)
    app.run(debug=True, host='0.0.0.0')
