import datetime
import os
from datetime import timedelta

from flask import Flask, render_template, redirect, url_for, request
from sqlalchemy import and_
from sqlalchemy_utils import database_exists

from models.models import db, Campaign, Source, DailyCampaign, DailySource, \
    CampaignRule, SourceRule, Binom, TrafficSource, TrafficSourceCredentials, PausedCampaign, PausedSource
from utils.api_utils import ApiUtils
from utils.rules_utils import set_campaign_rule_fields, save_rule_to_db, set_source_rule_fields
from utils.utils import read_config, init_logger
from web.service import paginate_data, get_pagination_metadata_from_query, get_path_args, render_empty_campaigns, \
    render_empty_sources, get_rule_fields, get_binom_fields, get_ts_credentials_fields
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
            'three_days': datetime.date.today() - timedelta(days=2),
            'week': datetime.date.today() - timedelta(days=6),
            }


@app.route('/campaigns/current', methods=['GET', 'POST'])
def current_campaigns():
    page_arg, start_arg, end_arg, ts_arg = get_path_args()
    campaign_query = Campaign.query.order_by(Campaign.name)

    today = str(datetime.datetime.today()).split(' ')[0]
    today_start = datetime.datetime.strptime(today + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    today_end = datetime.datetime.strptime(today + ' 23:59:59', '%Y-%m-%d %H:%M:%S')

    campaign_query = campaign_query.filter(
        and_(Campaign.fetched_at >= today_start,
             Campaign.fetched_at <= today_end))

    if ts_arg == 'push_house':
        traffic_sources = TrafficSource.query.filter_by(url='https://push.house/').all()
    else:
        traffic_sources = TrafficSource.query.filter_by(url='https://ungads.com/').all()

    traffic_sources = [ts.binom_ts_id for ts in traffic_sources]
    campaign_query = campaign_query.filter(Campaign.traffic_source.in_(traffic_sources))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, campaign_query)
    campaigns_list = paginate_data(pagination_metadata, campaign_query)

    if len(campaigns_list) == 0:
        return render_empty_campaigns('current_campaigns.html', ts_arg)

    table = CampaignTable(campaigns_list)

    return render_template('current_campaigns.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg,
                           ts=ts_arg)


@app.route('/campaigns/stats', methods=['GET', 'POST'])
def campaigns_stats():
    page_arg, start_arg, end_arg, ts_arg = get_path_args()

    if request.method == 'POST':
        try:
            days_campaigns = request.form['days_campaigns'] if request.form['days_campaigns'] else None

            if days_campaigns:
                if int(days_campaigns) == 1:
                    return redirect(url_for('current_campaigns', ts=ts_arg))

                start = datetime.date.today() - timedelta(int(days_campaigns) - 1)
                end = datetime.date.today()
                return redirect(url_for('campaigns_stats', start=start, end=end, ts=ts_arg))
        except KeyError:
            pass

    yesterday = datetime.datetime.now() - timedelta(days=1)
    campaign_query = DailyCampaign.query.order_by(DailyCampaign.name)
    current_campaign_query = Campaign.query.order_by(Campaign.name)

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

    if ts_arg == 'push_house':
        traffic_sources = TrafficSource.query.filter_by(url='https://push.house/').all()
    else:
        traffic_sources = TrafficSource.query.filter_by(url='https://ungads.com/').all()

    traffic_sources = [ts.binom_ts_id for ts in traffic_sources]
    campaign_query = campaign_query.filter(DailyCampaign.traffic_source.in_(traffic_sources))

    campaigns_list = campaign_query.all()
    current_campaigns_list = current_campaign_query.all()
    campaigns_list = campaigns_list + current_campaigns_list

    unique_campaigns_names = set()
    [unique_campaigns_names.add(camp.name) for camp in campaigns_list if camp.name not in unique_campaigns_names]

    campaigns_stats_list = []
    for name in unique_campaigns_names:
        campaign_stat = Campaign(name, 0, 0)

        for campaign in campaigns_list:
            if campaign.name == name:
                if campaign_stat.binom_source == 'undefined':
                    campaign_stat.binom_source = campaign.binom_source

                campaign_stat.traffic_source = campaign.traffic_source
                campaign_stat.revenue += campaign.revenue
                campaign_stat.binom_clicks += campaign.binom_clicks
                campaign_stat.lp_clicks += campaign.lp_clicks
                campaign_stat.leads += campaign.leads

                campaign_stat.cost += campaign.cost
                campaign_stat.clicks += campaign.clicks
                campaign_stat.impressions += campaign.impressions

        if campaign_stat.leads != 0:
            campaign_stat.payout = campaign_stat.revenue / campaign_stat.leads

        campaign_stat.profit = campaign_stat.revenue - campaign_stat.cost

        if campaign_stat.clicks != 0:
            campaign_stat.cpc = campaign_stat.cost / campaign_stat.clicks
            campaign_stat.epc = campaign_stat.revenue / campaign_stat.clicks

        if campaign_stat.binom_clicks != 0:
            campaign_stat.lp_ctr = campaign_stat.lp_clicks / campaign_stat.binom_clicks * 100

        if campaign_stat.cost != 0:
            campaign_stat.roi = campaign_stat.profit / campaign_stat.cost * 100

        if campaign_stat.impressions != 0:
            campaign_stat.ctr = campaign_stat.clicks / campaign_stat.impressions * 100
            campaign_stat.cpm = campaign_stat.cost / campaign_stat.impressions * 1000

        campaigns_stats_list.append(campaign_stat)

    if len(campaigns_stats_list) == 0:
        return render_empty_campaigns('campaigns_stats.html', ts_arg)

    campaigns_stats_list.sort(key=lambda x: x.name, reverse=True)

    table = CampaignStatsTable(campaigns_stats_list)

    return render_template('campaigns_stats.html',
                           table=table,
                           pagination_data=None,
                           start=start_arg,
                           end=end_arg,
                           ts=ts_arg)


@app.route('/campaigns/daily', methods=['GET', 'POST'])
def daily_campaigns():
    page_arg, start_arg, end_arg, ts_arg = get_path_args()

    if request.method == 'POST':
        try:
            days_campaigns = request.form['days_campaigns'] if request.form['days_campaigns'] else None

            if days_campaigns:
                if days_campaigns:
                    if int(days_campaigns) == 1:
                        return redirect(url_for('current_campaigns', ts=ts_arg))

                start = datetime.date.today() - timedelta(int(days_campaigns))
                end = start
                return redirect(url_for('daily_campaigns', start=start, end=end, ts=ts_arg))
        except KeyError:
            pass

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

    if ts_arg == 'push_house':
        traffic_sources = TrafficSource.query.filter_by(url='https://push.house/').all()
    else:
        traffic_sources = TrafficSource.query.filter_by(url='https://ungads.com/').all()

    traffic_sources = [ts.binom_ts_id for ts in traffic_sources]
    campaign_query = campaign_query.filter(DailyCampaign.traffic_source.in_(traffic_sources))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, campaign_query)
    campaigns_list = paginate_data(pagination_metadata, campaign_query)

    if len(campaigns_list) == 0:
        return render_empty_campaigns('daily_campaigns.html', ts_arg)

    table = DailyCampaignTable(campaigns_list)

    return render_template('daily_campaigns.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg,
                           ts=ts_arg)


@app.route('/campaigns/paused', methods=['GET', 'POST'])
def paused_campaigns():
    campaigns_list = PausedCampaign.query.all()

    if len(campaigns_list) == 0:
        return render_empty_campaigns('paused_campaigns.html', None)

    return render_template('paused_campaigns.html',
                           pagination_data=None,
                           paused_list=campaigns_list)


@app.route('/campaigns/paused/add', methods=['GET', 'POST'])
def campaigns_add_paused():
    if request.method == 'POST':
        campaign_name_param = request.form.get('campaign_name')
        ts_id = request.form.get('ts_id')

        if campaign_name_param and ts_id:
            ts = TrafficSource.query.filter_by(id=ts_id).first()
            if ',' in campaign_name_param:
                campaign_names = campaign_name_param.split(',')
                for campaign_name in campaign_names:
                    paused = PausedCampaign(campaign_name, ts)
                    db.session.add(paused)
            else:
                paused = PausedCampaign(campaign_name_param, ts)
                db.session.add(paused)

            db.session.commit()
            return redirect(url_for('paused_campaigns'))

    ts_list = TrafficSource.query.all()
    return render_template('add_paused_campaign.html',
                           form=None,
                           ts_list=ts_list)


@app.route('/campaigns/paused/delete/<ts_id>/<camp_name>', methods=['GET', 'POST'])
def campaigns_delete_paused(ts_id, camp_name):
    deleted_camp = PausedCampaign.query.filter_by(campaign_name=camp_name, ts_id=ts_id).first()
    if request.method == 'POST':
        db.session.delete(deleted_camp)
        db.session.commit()
        return redirect(url_for('paused_campaigns'))

    return render_template('delete_confirm.html',
                           message_title="Removing paused campaign",
                           message="Are you really want to delete paused campaign " + deleted_camp.campaign_name + " from local db (not TS) ?")


@app.route('/sources/current', methods=['GET', 'POST'])
def current_sources():
    page_arg, start_arg, end_arg, ts_arg = get_path_args()
    source_query = Source.query.order_by(Source.campaign_name)

    today = str(datetime.datetime.today()).split(' ')[0]
    today_start = datetime.datetime.strptime(today + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    today_end = datetime.datetime.strptime(today + ' 23:59:59', '%Y-%m-%d %H:%M:%S')

    source_query = source_query.filter(
        and_(Source.fetched_at >= today_start,
             Source.fetched_at <= today_end))

    if ts_arg == 'push_house':
        traffic_sources = TrafficSource.query.filter_by(url='https://push.house/').all()
    else:
        traffic_sources = TrafficSource.query.filter_by(url='https://ungads.com/').all()

    traffic_sources = [ts.binom_ts_id for ts in traffic_sources]
    source_query = source_query.filter(Source.traffic_source.in_(traffic_sources))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, source_query)
    source_list = paginate_data(pagination_metadata, source_query)

    if len(source_list) == 0:
        return render_empty_sources('current_sources.html', ts_arg)

    table = SourceTable(source_list)

    return render_template('current_sources.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg,
                           ts=ts_arg)


@app.route('/sources/stats', methods=['GET', 'POST'])
def sources_stats():
    page_arg, start_arg, end_arg, ts_arg = get_path_args()

    if request.method == 'POST':
        try:
            days_sources = request.form['days_sources'] if request.form['days_sources'] else None

            if days_sources:
                if days_sources:
                    if int(days_sources) == 1:
                        return redirect(url_for('current_sources', ts=ts_arg))

                start = datetime.date.today() - timedelta(int(days_sources))
                end = datetime.date.today() - timedelta(1)
                return redirect(url_for('sources_stats', start=start, end=end, ts=ts_arg))
        except KeyError:
            pass

    yesterday = datetime.datetime.now() - timedelta(days=1)
    source_query = DailySource.query.order_by(DailySource.campaign_name)
    current_source_query = Source.query.order_by(Source.campaign_name)

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

    if ts_arg == 'push_house':
        traffic_sources = TrafficSource.query.filter_by(url='https://push.house/').all()
    else:
        traffic_sources = TrafficSource.query.filter_by(url='https://ungads.com/').all()

    traffic_sources = [ts.binom_ts_id for ts in traffic_sources]
    source_query = source_query.filter(DailySource.traffic_source.in_(traffic_sources))

    sources_list = source_query.all()
    current_source_list = current_source_query.all()
    sources_list = sources_list + current_source_list

    unique_names = set()
    [unique_names.add((source.name, source.campaign_name)) for source in sources_list if
     (source.name, source.campaign_name) not in unique_names]

    sources_stats_list = []
    for names in unique_names:
        source_stat = Source(names[0], names[1], 0, 0)

        source_list = source_query.filter(
            and_(DailySource.name == names[0],
                 DailySource.campaign_name == names[1])).all()
        current_source_list = current_source_query.filter(
            and_(Source.name == names[0],
                 Source.campaign_name == names[1])).all()
        source_list = source_list + current_source_list

        for source in source_list:
            if source_stat.binom_source == 'undefined':
                source_stat.binom_source = source.binom_source

            source_stat.traffic_source = source.traffic_source
            source_stat.revenue += source.revenue
            source_stat.binom_clicks += source.binom_clicks
            source_stat.lp_clicks += source.lp_clicks
            source_stat.leads += source.leads

            source_stat.cost += source.cost
            source_stat.clicks += source.clicks
            source_stat.impressions += source.impressions

            if source_stat.leads != 0:
                source_stat.payout = source_stat.revenue / source_stat.leads

            source_stat.profit = source_stat.revenue - source_stat.cost

            if source_stat.clicks != 0:
                source_stat.cpc = source_stat.cost / source_stat.clicks
                source_stat.epc = source_stat.revenue / source_stat.clicks

            if source_stat.binom_clicks != 0:
                source_stat.lp_ctr = source_stat.lp_clicks / source_stat.binom_clicks * 100

            if source_stat.cost != 0:
                source_stat.roi = source_stat.profit / source_stat.cost * 100

            if source_stat.impressions != 0:
                source_stat.ctr = source_stat.clicks / source_stat.impressions * 100
                source_stat.cpm = source_stat.cost / source_stat.impressions * 1000

        sources_stats_list.append(source_stat)

    sources_stats_list.sort(key=lambda x: x.campaign_name)

    if len(sources_stats_list) == 0:
        return render_empty_sources('sources_stats.html', ts_arg)

    table = SourceStatsTable(sources_stats_list)

    return render_template('sources_stats.html',
                           table=table,
                           pagination_data=None,
                           start=start_arg,
                           end=end_arg,
                           ts=ts_arg)


@app.route('/sources/daily', methods=['GET', 'POST'])
def daily_sources():
    page_arg, start_arg, end_arg, ts_arg = get_path_args()

    if request.method == 'POST':
        try:
            days_sources = request.form['days_sources'] if request.form['days_sources'] else None

            if days_sources:
                if days_sources:
                    if int(days_sources) == 1:
                        return redirect(url_for('current_sources', ts=ts_arg))

                start = datetime.date.today() - timedelta(int(days_sources))
                end = start
                return redirect(url_for('daily_sources', start=start, end=end, ts=ts_arg))
        except KeyError:
            pass

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

    if ts_arg == 'push_house':
        traffic_sources = TrafficSource.query.filter_by(url='https://push.house/').all()
    else:
        traffic_sources = TrafficSource.query.filter_by(url='https://ungads.com/').all()

    traffic_sources = [ts.binom_ts_id for ts in traffic_sources]
    sources_query = sources_query.filter(DailySource.traffic_source.in_(traffic_sources))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, sources_query)
    sources_list = paginate_data(pagination_metadata, sources_query)

    if len(sources_list) == 0:
        return render_empty_sources('daily_sources.html', ts_arg)

    table = DailySourceTable(sources_list)

    return render_template('daily_sources.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg,
                           ts=ts_arg)


@app.route('/sources/paused', methods=['GET'])
def paused_sources():
    sources_list = PausedSource.query.all()

    if len(sources_list) == 0:
        return render_empty_sources('paused_campaigns.html', None)

    return render_template('paused_sources.html',
                           pagination_data=None,
                           paused_list=sources_list)


@app.route('/sources/paused/add', methods=['GET', 'POST'])
def sources_add_paused():
    if request.method == 'POST':
        source_name_param = request.form.get('source_name')
        campaign_name = request.form.get('campaign_name')
        ts_id = request.form.get('ts_id')

        if source_name_param and campaign_name and ts_id:
            ts = TrafficSource.query.filter_by(id=ts_id).first()
            if ',' in source_name_param:
                source_names = source_name_param.split(',')
                for source_name in source_names:
                    paused = PausedSource(source_name, campaign_name, ts)
                    db.session.add(paused)
            else:
                paused = PausedSource(source_name_param, campaign_name, ts)
                db.session.add(paused)
            db.session.commit()
            return redirect(url_for('paused_sources'))

    ts_list = TrafficSource.query.all()
    return render_template('add_paused_source.html',
                           form=None,
                           ts_list=ts_list)


@app.route('/sources/paused/delete/<ts_id>/<camp_name>/<source_name>', methods=['GET', 'POST'])
def sources_delete_paused(ts_id, camp_name, source_name):
    deleted_source = PausedSource.query.filter_by(source_name=source_name, campaign_name=camp_name, ts_id=ts_id).first()
    if request.method == 'POST':
        db.session.delete(deleted_source)
        db.session.commit()
        return redirect(url_for('paused_sources'))

    return render_template('delete_confirm.html',
                           message_title="Removing paused source",
                           message="Are you really want to delete paused source " + deleted_source.source_name + " from local db (not TS) ?")


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

    ts_list = TrafficSource.query.all()
    return render_template('add_campaign_rule.html',
                           form=None,
                           ts_list=ts_list)


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

    ts_list = TrafficSource.query.all()
    return render_template('add_source_rule.html',
                           form=None,
                           ts_list=ts_list)


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


@app.route('/logs', methods=['GET'])
def logs():
    dir_list = os.listdir('logs')
    dir_list.remove('rules.log')

    dir_list.sort(reverse=True)

    logs_data = []

    with open('logs/rules.log', 'r') as f:
        log = f.readlines()
        log = list(reversed(log))
        logs_data.append(log)

    for log_file in dir_list:
        try:
            with open('logs/' + log_file, 'r') as f:
                log = f.readlines()
                log = list(reversed(log))
                logs_data.append(log)
        except FileNotFoundError:
            pass

    logs_data = [item for sublist in logs_data for item in sublist]
    ' '.join(logs_data)
    return render_template('logs.html', logs=logs_data)


@app.route('/binoms', methods=['GET', 'POST'])
def binoms():
    if request.method == 'POST':
        if request.form.get('update_ts_for'):
            update_ts_for = request.form.get('update_ts_for')
            binom = Binom.query.filter_by(id=update_ts_for).first()
            traffic_sources = api.get_binom_traffic_sources(binom)
            for ts in traffic_sources:
                if not TrafficSource.query.filter_by(binom_id=binom.id, binom_ts_id=ts.binom_ts_id).first():
                    db.session.add(ts)

            db.session.commit()
        else:
            ts_id = request.form.get('ts_id')
            credentials_id = request.form.get('credentials')

            ts = TrafficSource.query.filter_by(id=ts_id).first()
            ts.credentials_id = credentials_id
            db.session.add(ts)
            db.session.commit()

            return redirect(url_for('binoms'))

    binoms_list = Binom.query.all()
    ts_list = TrafficSource.query.all()
    creds_list = TrafficSourceCredentials.query.all()
    return render_template('binoms.html',
                           binoms=binoms_list,
                           traffic_sources=ts_list,
                           creds_list=creds_list)


@app.route('/binoms/add', methods=['GET', 'POST'])
def add_binom():
    if request.method == 'POST':
        binom_dict = get_binom_fields()
        binom = Binom(binom_dict.get('name'), binom_dict.get('url'), binom_dict.get('api_key'))
        db.session.add(binom)
        db.session.commit()

        binom = Binom.query.filter_by(name=binom.name, url=binom.url, api_key=binom.api_key).first()
        traffic_sources = api.get_binom_traffic_sources(binom)
        for ts in traffic_sources:
            db.session.add(ts)

        db.session.commit()
        return redirect(url_for('binoms'))

    return render_template('add_binom.html')


@app.route('/binoms/delete/<binom_id>', methods=['GET', 'POST'])
def delete_binom(binom_id):
    deleted_binom = Binom.query.filter_by(id=binom_id).first()
    if request.method == 'POST':
        db.session.delete(deleted_binom)
        db.session.commit()
        return redirect(url_for('binoms'))

    return render_template('delete_confirm.html',
                           message_title="Removing Binom",
                           message="Are you really want to delete Binom " + deleted_binom.name + "?")


@app.route('/ts_credentials', methods=['GET'])
def ts_credentials():
    creds_list = TrafficSourceCredentials.query.all()
    return render_template('ts_credentials.html', creds_list=creds_list)


@app.route('/ts_credentials/add', methods=['GET', 'POST'])
def add_ts_credentials():
    if request.method == 'POST':
        creds_dict = get_ts_credentials_fields()
        creds = TrafficSourceCredentials(creds_dict.get('name'), creds_dict.get('url'), creds_dict.get('api_key'))
        db.session.add(creds)
        db.session.commit()
        return redirect(url_for('ts_credentials'))

    return render_template('add_ts_credentials.html')


@app.route('/ts_credentials/delete/<creds_id>', methods=['GET', 'POST'])
def delete_ts_credentials(creds_id):
    deleted_creds = TrafficSourceCredentials.query.filter_by(id=creds_id).first()
    if request.method == 'POST':
        db.session.delete(deleted_creds)
        db.session.commit()
        return redirect(url_for('ts_credentials'))

    return render_template('delete_confirm.html',
                           message_title="Removing TrafficSource Credentials",
                           message="Are you really want to delete credentials for " + deleted_creds.url + "?")


if __name__ == '__main__':
    config = read_config()
    api = ApiUtils(config)
    init_logger()

    db.init_app(app)
    app.run(debug=True, host='0.0.0.0')
