import math

from flask import request, render_template
from sqlalchemy import func


def get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count


def get_path_args():
    page = request.args.get('page', 1, type=int)
    start = request.args.get('start')
    end = request.args.get('end')
    ts = request.args.get('ts', 'push_house', type=str)

    return page, start, end, ts


def get_pagination_metadata_from_query(page, data_query):
    rows_per_page = 12
    last_page = math.ceil(data_query.count() / rows_per_page)

    return {'current': page, 'next': page + 1, 'previous': page - 1,
            'first': 1, 'last': last_page, 'rows_per_page': rows_per_page}


def get_pagination_metadata_from_count(page, count):
    rows_per_page = 12
    last_page = math.ceil(count / rows_per_page)

    return {'current': page, 'next': page + 1, 'previous': page - 1,
            'first': 1, 'last': last_page, 'rows_per_page': rows_per_page}


def paginate_data(metadata, query):
    query = query.paginate(page=metadata['current'], per_page=metadata['rows_per_page'])

    return query.items


def render_empty_campaigns(template, ts):
    return render_template(template,
                           table='<p class="subtitle is-italic" style="padding:20px;">No campaigns for your request. Enter some parameters in rightside menu.</p>',
                           pagination_data=None,
                           ts=ts)


def render_empty_sources(template, ts):
    return render_template(template,
                           table='<p class="subtitle is-italic" style="padding:20px;">No sources for your request. Enter some parameters in rightside menu.</p>',
                           pagination_data=None,
                           ts=ts)


def get_rule_fields():
    rule = {
        'conditions': request.form.get('conditions'),
        'name': request.form.get('name'),
        'campaign_name': request.form.get('campaign_name'),
        'param1': request.form.get('param1'),
        'sign1': request.form.get('sign1'),
        'value1': request.form.get('value1'),
        'param2': request.form.get('param2'),
        'sign2': request.form.get('sign2'),
        'value2': request.form.get('value2'),
        'param3': request.form.get('param3'),
        'sign3': request.form.get('sign3'),
        'value3': request.form.get('value3'),
        'param4': request.form.get('param4'),
        'sign4': request.form.get('sign4'),
        'value4': request.form.get('value4'),
        'days': request.form.get('days'),
        'action': request.form.get('action')
    }

    return rule


def get_binom_fields():
    binom = {
        'name': request.form.get('name'),
        'url': request.form.get('url'),
        'api_key': request.form.get('api_key'),
    }

    return binom


def get_ts_credentials_fields():
    creds = {
        'name': request.form.get('name'),
        'url': request.form.get('url'),
        'api_key': request.form.get('api_key'),
    }

    return creds
