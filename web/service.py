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

    return page, start, end


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


def render_empty_campaigns(template):
    return render_template(template,
                           table='<p class="subtitle is-italic" style="padding:20px;">No campaigns for your request. Enter some parameters in rightside menu.</p>',
                           pagination_data=None)


def render_empty_sources(template):
    return render_template(template,
                           table='<p class="subtitle is-italic" style="padding:20px;">No sources for your request. Enter some parameters in rightside menu.</p>',
                           pagination_data=None)
