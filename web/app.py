import datetime
from datetime import timedelta

from flask import Flask, render_template, redirect, url_for, request
from sqlalchemy import desc, and_
from sqlalchemy_utils import database_exists

from bin.api_utils import get_campaigns, get_sources
from bin.utils import read_config, init_logger
from models import db, Campaign, TrafficSource
from web.service import paginate_data, get_pagination_metadata_from_query, get_path_args, render_empty_campaigns, \
    render_empty_sources
from web.tables import CampaignTable, TrafficSourceTable, ExtractedCampaignTable, ExtractedTrafficSourceTable

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../data/db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
    with app.test_request_context():
        db.init_app(app)
        db.create_all()


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
                start = datetime.date.today() - timedelta(int(days_campaigns))
                end = datetime.date.today() - timedelta(1)
                return redirect(url_for('extracted_campaigns', start=start, end=end))
        except KeyError:
            pass

    page_arg, start_arg, end_arg = get_path_args()

    campaigns = None
    if start_arg and end_arg:
        campaigns = get_campaigns(start_date=start_arg, end_date=end_arg)

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

    page_arg, start_arg, end_arg = get_path_args()

    yesterday = datetime.datetime.now() - timedelta(days=1)
    campaign_query = Campaign.query.order_by(desc(Campaign.fetched_at))

    if start_arg and end_arg:
        start = start_arg + ' 00:00:00'
        end = end_arg + ' 23:59:59'
        campaign_query = campaign_query.filter(
            and_(Campaign.fetched_at >= start,
                 Campaign.fetched_at <= end))
    else:
        campaign_query = campaign_query.filter(
            and_(Campaign.fetched_at >= yesterday,
                 Campaign.fetched_at <= yesterday))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, campaign_query)
    campaigns_list = paginate_data(pagination_metadata, campaign_query)

    if len(campaigns_list) == 0:
        return render_empty_campaigns('filtered_campaigns.html')

    table = CampaignTable(campaigns_list)

    return render_template('filtered_campaigns.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg)


@app.route('/sources/current', methods=['GET', 'POST'])
def current_sources():
    page_arg, start_arg, end_arg = get_path_args()
    source_query = TrafficSource.query.order_by(desc(TrafficSource.fetched_at))

    today = str(datetime.datetime.today()).split(' ')[0]
    today_start = datetime.datetime.strptime(today + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
    today_end = datetime.datetime.strptime(today + ' 23:59:59', '%Y-%m-%d %H:%M:%S')

    source_query = source_query.filter(
        and_(TrafficSource.fetched_at >= today_start,
             TrafficSource.fetched_at <= today_end))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, source_query)
    source_list = paginate_data(pagination_metadata, source_query)

    if len(source_list) == 0:
        return render_empty_sources('current_sources.html')

    table = TrafficSourceTable(source_list)

    return render_template('current_sources.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg)


@app.route('/sources/extracted', methods=['GET', 'POST'])
def extracted_sources():
    if request.method == 'POST':
        try:
            days_campaigns = request.form['days_sources'] if request.form['days_sources'] else None

            if days_campaigns:
                start = datetime.date.today() - timedelta(int(days_campaigns))
                end = datetime.date.today() - timedelta(1)
                return redirect(url_for('extracted_sources', start=start, end=end))
        except KeyError:
            pass

    page_arg, start_arg, end_arg = get_path_args()

    sources = None
    if start_arg and end_arg:
        campaigns = get_campaigns(start_date=start_arg, end_date=end_arg)
        sources = get_sources(campaigns, start_date=start_arg, end_date=end_arg)

    if not sources:
        return render_empty_sources('extracted_sources.html')

    table = ExtractedTrafficSourceTable(sources)

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

    page_arg, start_arg, end_arg = get_path_args()

    yesterday = datetime.datetime.now() - timedelta(days=1)
    sources_query = TrafficSource.query.order_by(desc(TrafficSource.fetched_at))

    if start_arg and end_arg:
        start = start_arg + ' 00:00:00'
        end = end_arg + ' 23:59:59'
        sources_query = sources_query.filter(
            and_(TrafficSource.fetched_at >= start,
                 TrafficSource.fetched_at <= end))
    else:
        sources_query = sources_query.filter(
            and_(TrafficSource.fetched_at >= yesterday,
                 TrafficSource.fetched_at <= yesterday))

    pagination_metadata = get_pagination_metadata_from_query(page_arg, sources_query)
    sources_list = paginate_data(pagination_metadata, sources_query)

    if len(sources_list) == 0:
        return render_empty_sources('filtered_sources.html')

    table = TrafficSourceTable(sources_list)

    return render_template('filtered_sources.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg)


@app.route('/')
def root():
    return redirect(url_for('current_campaigns'))


def main():
    read_config()
    init_logger()

    db.init_app(app)
    app.run(debug=True, host='0.0.0.0')
