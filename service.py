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

    if start and end:
        start = start + ' 00:00:00'
        end = end + ' 23:59:59'

    return page, start, end


def get_pagination_metadata(page, data_query):
    rows_per_page = 12
    last_page = math.ceil(data_query.count() / rows_per_page)

    return {'current': page, 'next': page + 1, 'previous': page - 1,
            'first': 1, 'last': last_page, 'rows_per_page': rows_per_page}


def paginate_data(metadata, query):
    query = query.paginate(page=metadata['current'], per_page=metadata['rows_per_page'])

    return query.items


def render_empty_campaigns():
    return render_template('stats_campaigns.html',
                           table='<p class="subtitle is-italic" style="padding:20px;">Sorry, no campaigns for your request.</p>',
                           pagination_data=None)


def render_empty_sources():
    return render_template('stats_sources.html',
                           table='<p class="subtitle is-italic" style="padding:20px;">Sorry, no sources for your request.</p>',
                           pagination_data=None)
