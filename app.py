import datetime
from datetime import timedelta

from flask import Flask, render_template, redirect, url_for
from sqlalchemy import desc, and_
from sqlalchemy_utils import database_exists

from models import db, Campaign, TrafficSource
from service import paginate_data, get_pagination_metadata, get_path_args, render_empty_campaigns, render_empty_sources
from tables import CampaignTable, TrafficSourceTable

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
    with app.test_request_context():
        db.init_app(app)
        db.create_all()


@app.context_processor
def inject_dates():
    return {'today': datetime.date.today(),
            'yesterday': datetime.date.today() - timedelta(days=1),
            'three_days': datetime.date.today() - timedelta(days=2),
            'week': datetime.date.today() - timedelta(days=6),
            }


@app.route('/stats/campaigns')
def stats_campaigns():
    page_arg, start_arg, end_arg = get_path_args()
    campaign_query = Campaign.query.order_by(desc(Campaign.fetched_at))

    if start_arg and end_arg:
        campaign_query = campaign_query.filter(
            and_(Campaign.fetched_at >= start_arg,
                 Campaign.fetched_at <= end_arg))

    pagination_metadata = get_pagination_metadata(page_arg, campaign_query)
    campaigns_list = paginate_data(pagination_metadata, campaign_query)

    if len(campaigns_list) == 0:
        return render_empty_campaigns()

    table = CampaignTable(campaigns_list)

    return render_template('stats_campaigns.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg)


@app.route('/stats/sources')
def stats_sources():
    page_arg, start_arg, end_arg = get_path_args()
    source_query = TrafficSource.query.order_by(desc(TrafficSource.fetched_at))

    if start_arg and end_arg:
        source_query = source_query.filter(
            and_(TrafficSource.fetched_at >= start_arg,
                 TrafficSource.fetched_at <= end_arg))

    pagination_metadata = get_pagination_metadata(page_arg, source_query)
    sources_list = paginate_data(pagination_metadata, source_query)

    if len(sources_list) == 0:
        return render_empty_sources()

    table = TrafficSourceTable(sources_list)

    return render_template('stats_sources.html',
                           table=table,
                           pagination_data=pagination_metadata,
                           start=start_arg,
                           end=end_arg)


@app.route('/')
def root():
    return redirect(url_for('stats_campaigns'))


if __name__ == '__main__':
    db.init_app(app)
    app.run(host='0.0.0.0')
