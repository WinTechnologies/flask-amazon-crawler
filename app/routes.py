import os
import requests
import re
import sys
import datetime
import xlsxwriter
import pandas as pd
from io import BytesIO

from querystring_parser import parser
from flask import Flask, render_template, request, Blueprint, jsonify, redirect, send_file, session
from sqlalchemy import desc, asc
from datetime import datetime, timedelta
from celery.utils.log import get_logger

from app import db
from app.models.asin import Asin
from datatables import ColumnDT, DataTables
from app.tasks.asin_task import save_data
from app.forms.search import SearchForm
from app.helper import max_value, get_by_time, get_by_date, get_by_month, get_ready_excel, get_by_week

bp = Blueprint("all", __name__)
app_root = os.path.dirname(os.path.abspath(__file__))

@bp.route("/")
def index():
    search_form = SearchForm()
    return render_template('index.html', form=search_form)

@bp.route('/analysis')
def analysis():
    return render_template('analysis.html')

@bp.route('/uploader', methods=['GET', 'POST'])
def uploader():
    target = os.path.join(app_root, 'uploads')
    if not os.path.isdir(target):
        os.mkdir(target)

    f = request.files.get('input')
    file_name = f.filename

    # current - count
    current_count = db.session.query(Asin).count()

    if request.method == 'POST' and file_name != '':
        destination = os.path.join(target, file_name)
        f.save(destination)

        with open(destination, 'r') as file:
            lines = file.readlines()

        crawler_count = 0
        for line in lines:
            cc=line.split()
            try:
                save_data.apply_async((cc[0], cc[1]), retry=False)
            except save_data.OperationalError as exec:
                logger.exception('Sending task raised: %r', exc)
                new_asin = Asin(
                    site_url=cc[0],
                    asin=cc[1],
                    review_rating='',
                    quantity='',
                    unit='',
                    sell_price='',
                    link='httpss://' + cc[0] + '/dp/' + cc[1],
                    status='OperationalError',
                    description='Connection Error'
                )
                db.session.add(new_asin)
                try:
                    db.session.commit()
                except:
                    db.session.rollback()
                finally:
                    db.session.close()

            crawler_count = crawler_count + 1

        result = {
            'count': crawler_count,
            'status': 'success',
            'message': '<b>' + str(crawler_count) + '</b> crawlers are running in background, you can check them to refresh the page.',
            'expected_count': current_count + crawler_count
        }
    else:
        result = {
            'count': 0,
            'status': 'error',
            'message': 'It seems like the file format has not matched to the standard input.',
            'expected_count': current_count
        }

    return result

@bp.route('/progress/<int:count>')
def progress(count):
    search_form = SearchForm()
    current_count = db.session.query(Asin).count()
    return render_template('index.html', form=search_form, current_count=current_count)

@bp.route('/search', methods=['POST'])
def search():
    search_form = SearchForm()
    if search_form.validate():
        query = search_form.query.data
        query = db.session.query(Asin).filter( Asin.site_url.like('%'+query + '%') | Asin.asin.like('%' + query + '%'))
        result = query.all()
        return render_template('search_result.html', result=result)

@bp.route('/graph', methods=['GET', 'POST'])
def graph():
    _json = request.json
    start_date = _json['start']
    end_date = _json['end']
    asin = _json['asin']
    x_axis = _json['x_axis']

    if x_axis == 'time':
        result = get_by_time(_json)
    elif x_axis == 'date':
        result = get_by_date(_json)
    elif x_axis == 'week':
        result = get_by_week(_json)
    elif x_axis == 'month':
        result = get_by_month(_json)

    response = jsonify(result)
    response.status_code = 200
    return response

@bp.route('/get_asin', methods=['GET'])
def get_asin():
    search = request.args.get('q')
    query = db.session.query(Asin.asin.distinct()).filter(Asin.asin.like('%' + str(search) + '%'))
    results = [asin[0] for asin in query.limit(10).all()]
    return jsonify(results=results)

@bp.route('/download/<string:from_date>/<string:to_date>/<string:asin>/<string:site>', methods=['GET'])
def download(from_date, to_date, asin, site):
    try:
        start = datetime.strptime(from_date, '%Y-%m-%d')
        end = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
    except ValueError:
        start = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=1)

    _json = {
        'start': start,
        'end': end,
        'asin': asin,
        'site': site
    }

    results = get_ready_excel(_json)
    df = pd.DataFrame(columns=['ASIN', 'Price', '+/-(Price)', 'Rating', '+/-(Rating)', 'Review Quality', '抓取时间'])
    index=0
    for row in results:
        index+=1
        df = df.append({
                'ASIN': row.get('asin'),
                'Price':row.get('price'),
                '+/-(Price)': row.get('diff_price'),
                'Rating': row.get('review'),
                '+/-(Rating)': row.get('diff_review'),
                'Review Quality': row.get('quantity'),
                '抓取时间': row.get('date')
                },ignore_index=True)

    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    df.to_excel(writer, sheet_name='ASIN', float_format="%.2f", index=False)
    workbook = writer.book
    worksheet = writer.sheets['ASIN']

    green_format = workbook.add_format({'font_color': '#29d96a'})
    red_format = workbook.add_format({'font_color': '#c92c1e'})

    worksheet.conditional_format('C2:D367', {
        'type': 'cell',
        'criteria': '>',
        'value': '0',
        'format': green_format
    })
    worksheet.conditional_format('C2:D367', {
        'type': 'cell',
        'criteria': '<',
        'value': '0',
        'format': red_format
    })

    worksheet.conditional_format('E2:F367', {
        'type': 'cell',
        'criteria': '>',
        'value': '0',
        'format': green_format
    })
    worksheet.conditional_format('E2:F367', {
        'type': 'cell',
        'criteria': '<',
        'value': '0',
        'format': red_format
    })


    writer.save()
    output.seek(0)
    return send_file(output, attachment_filename='output.xlsx', as_attachment=True)

@bp.route('/get_data')
def get_data():
    from app.helper import dt_to_str
    columns = [
        ColumnDT(Asin.id),
        ColumnDT(Asin.site_url),
        ColumnDT(Asin.asin),
        ColumnDT(Asin.review_rating),
        ColumnDT(Asin.quantity),
        ColumnDT(Asin.unit),
        ColumnDT(Asin.sell_price),
        ColumnDT(Asin.link),
        ColumnDT(Asin.created_at),
        ColumnDT(Asin.status),
        ColumnDT(Asin.description)
    ]

    args = parser.parse(request.query_string)

    order = args['order']
    order_index = order[0]['column']
    dir_asc = order[0]['dir']

    if order_index == 1:
        order = Asin.site_url
    elif order_index == 2:
        order = Asin.asin
    elif order_index == 3:
        order = Asin.review_rating
    elif order_index == 4:
        order = Asin.quantity
    elif order_index == 5:
        order = Asin.sell_price
    elif order_index == 6:
        order = Asin.link
    elif order_index == 7:
        order = Asin.link
    elif order_index == 8:
        order = Asin.created_at
    elif order_index == 9:
        order = Asin.status
    elif order_index == 10:
        order = Asin.description
    else:
        order = Asin.id

    if dir_asc == 'desc':
        order_by = desc(order)
    else:
        order_by = asc(order)

    search_value = args['search']['value']

    if search_value != '':
        query = db.session.query().select_from(Asin)
    else:
        query = db.session.query().select_from(Asin).filter( Asin.site_url.like('%'+search_value + '%') | Asin.asin.like('%' + search_value + '%'))

        query = query.order_by(order_by)
    params = request.args.to_dict()
    rowTable = DataTables(params, query, columns)

    # returns what is needed by DataTable
    return jsonify(rowTable.output_result())

@bp.route("/test")
def test():
    domain = 'amazon.com'
    asin_symbol = 'B081GTRKVY'

    new_asin = Asin(
            site_url=domain,
            asin=asin_symbol,
            review_rating='-',
            quantity='-',
            unit='-',
            sell_price='-',
            link='https://' + domain + '/dp/' + asin_symbol,
            status='pending',
            description=''
        )

    db.session.add(new_asin)
    db.session.commit()

    try:
        new_pk_id = new_asin.id

        result = crawler_result(domain, asin_symbol)

        asin = Asin.query.filter(Asin.id == new_pk_id).first()
        asin.review_rating = result.get('review')
        asin.quantity = result.get('quantity')
        asin.unit = result.get('unit')
        asin.sell_price = result.get('sell_price')
        asin.status = result.get('status')
        asin.description = result.get('description')

        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()


    return 'tttttttttttttttt'

