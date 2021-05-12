import datetime
import os
from datetime import timedelta

from flask import Flask, render_template, redirect, url_for, request
from sqlalchemy import desc, and_
from sqlalchemy_utils import database_exists

from models.models import db, Campaign, Source, ExtractedCampaign, ExtractedSource, DailyCampaign, DailySource, \
    CampaignRule
from utils.api_utils import ApiUtils
from utils.rules_utils import set_rules_field, save_rule_to_db
from utils.utils import read_config, init_logger
from web.service import paginate_data, get_pagination_metadata_from_query, get_path_args, render_empty_campaigns, \
    render_empty_sources, get_rule_fields
from web.tables import CampaignTable, SourceTable, ExtractedCampaignTable, ExtractedSourceTable, FilteredSourceTable, \
    FilteredCampaignTable

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
    page_arg, start_arg, end_arg, days = get_path_args()
    campaign_query = Campaign.query.order_by(desc(Campaign.fetched_at))

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


@app.route('/campaigns/extracted', methods=['GET', 'POST'])
def extracted_campaigns():
    if request.method == 'POST':
        try:
            days_campaigns = request.form['days_campaigns'] if request.form['days_campaigns'] else None

            if days_campaigns:
                return redirect(url_for('extracted_campaigns', days=days_campaigns))
        except KeyError:
            pass

    page_arg, start_arg, end_arg, days = get_path_args()
    campaign_query = ExtractedCampaign.query.order_by(desc(ExtractedCampaign.fetched_at))

    campaigns = None
    if days:
        campaigns = campaign_query.filter_by(last_days=days).all()

    if not campaigns:
        return render_empty_campaigns('extracted_campaigns.html')

    table = ExtractedCampaignTable(campaigns)

    return render_template('extracted_campaigns.html',
                           table=table,
                           pagination_data=None,
                           start=start_arg,
                           end=end_arg)


@app.route('/campaigns/filtered', methods=['GET', 'POST'])
def filtered_campaigns():
    if request.method == 'POST':
        try:
            days_campaigns = request.form['days_campaigns'] if request.form['days_campaigns'] else None

            if days_campaigns:
                start = datetime.date.today() - timedelta(int(days_campaigns))
                end = datetime.date.today() - timedelta(1)
                return redirect(url_for('filtered_campaigns', start=start, end=end))
        except KeyError:
            pass

    page_arg, start_arg, end_arg, days = get_path_args()

    yesterday = datetime.datetime.now() - timedelta(days=1)
    campaign_query = DailyCampaign.query.order_by(desc(DailyCampaign.fetched_at))

    if start_arg and end_arg:
        start = start_arg + ' 00:00:00'
        end = end_arg + ' 23:59:59'
        campaign_query = campaign_query.filter(
            and_(DailyCampaign.fetched_at >= start,
                 DailyCampaign.fetched_at <= end))
    else:
        campaign_query = campaign_query.filter(
            and_(DailyCampaign.fetched_at >= yesterday,
                 DailyCampaign.fetched_at <= yesterday))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, campaign_query)
    campaigns_list = paginate_data(pagination_metadata, campaign_query)

    if len(campaigns_list) == 0:
        return render_empty_campaigns('filtered_campaigns.html')

    table = FilteredCampaignTable(campaigns_list)

    return render_template('filtered_campaigns.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg)


@app.route('/sources/current', methods=['GET', 'POST'])
def current_sources():
    page_arg, start_arg, end_arg, days = get_path_args()
    source_query = Source.query.order_by(desc(Source.fetched_at))

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


@app.route('/sources/extracted', methods=['GET', 'POST'])
def extracted_sources():
    if request.method == 'POST':
        try:
            days_sources = request.form['days_sources'] if request.form['days_sources'] else None

            if days_sources:
                return redirect(url_for('extracted_sources', days=days_sources))
        except KeyError:
            pass

    page_arg, start_arg, end_arg, days = get_path_args()
    source_query = ExtractedSource.query.order_by(desc(ExtractedSource.fetched_at))

    sources = None
    if days:
        sources = source_query.filter_by(last_days=days).all()

    if not sources:
        return render_empty_sources('extracted_sources.html')

    table = ExtractedSourceTable(sources)

    return render_template('extracted_sources.html',
                           table=table,
                           pagination_data=None,
                           start=start_arg,
                           end=end_arg)


@app.route('/sources/filtered', methods=['GET', 'POST'])
def filtered_sources():
    if request.method == 'POST':
        try:
            days_campaigns = request.form['days_sources'] if request.form['days_sources'] else None

            if days_campaigns:
                start = datetime.date.today() - timedelta(int(days_campaigns))
                end = datetime.date.today() - timedelta(1)
                return redirect(url_for('filtered_sources', start=start, end=end))
        except KeyError:
            pass

    page_arg, start_arg, end_arg, days = get_path_args()

    yesterday = datetime.datetime.now() - timedelta(days=1)
    sources_query = DailySource.query.order_by(desc(DailySource.fetched_at))

    if start_arg and end_arg:
        start = start_arg + ' 00:00:00'
        end = end_arg + ' 23:59:59'
        sources_query = sources_query.filter(
            and_(DailySource.fetched_at >= start,
                 DailySource.fetched_at <= end))
    else:
        sources_query = sources_query.filter(
            and_(DailySource.fetched_at >= yesterday,
                 DailySource.fetched_at <= yesterday))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, sources_query)
    sources_list = paginate_data(pagination_metadata, sources_query)

    if len(sources_list) == 0:
        return render_empty_sources('filtered_sources.html')

    table = FilteredSourceTable(sources_list)

    return render_template('filtered_sources.html',
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
    return render_template('sources_rules.html',
                           table=None,
                           pagination_data=None,
                           start=None,
                           end=None)


@app.route('/campaigns/rules/add', methods=['GET', 'POST'])
def campaigns_add_rule():
    if request.method == 'POST':
        rule_dict = get_rule_fields()
        print(rule_dict)
        rule = set_rules_field(rule_dict)
        save_rule_to_db(rule)

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
        rule = set_rules_field(rule_dict)
        save_rule_to_db(rule)

    return render_template('add_campaign_rule.html',
                           form=None)


if __name__ == '__main__':
    config = read_config()
    api = ApiUtils(config)
    init_logger()

    db.init_app(app)
    app.run(debug=True, host='0.0.0.0')
