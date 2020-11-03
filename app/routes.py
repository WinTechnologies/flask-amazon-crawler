import os
import requests
import re
import sys

from flask import Flask, render_template, request, Blueprint, jsonify, redirect, send_file, session
from sqlalchemy import desc
from datetime import datetime, timedelta

import pandas as pd
from app import db
from app.models.asin import Asin
from datatables import ColumnDT, DataTables
from app.tasks.asin_task import save_data
from app.forms.search import SearchForm

bp = Blueprint("all", __name__)
app_root = os.path.dirname(os.path.abspath(__file__))

@bp.route("/")
def index():
    search_form = SearchForm()
    return render_template('index.html', form=search_form)

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
            save_data.delay(cc[0], cc[1])

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

@bp.route('/to_excel/<string:from_date>/<string:to_date>', methods=['GET'])
def to_excel(from_date, to_date):
    from_date = datetime.strptime(from_date, '%Y-%m-%d')
    to_date = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)

    query = db.session.query(Asin).filter(
        Asin.created_at >= from_date,
        Asin.created_at < to_date)
    results = query.all()

    df = pd.DataFrame(columns=['Amazon Site','ASIN','Review Rating','Quantity of Reviews','Monteray Unit','Selling Price','Link'])
    filename = "/autos.xlsx"
    for row in results:
        df = df.append({'Amazon Site': row.site_url, 'ASIN': row.asin, 'Review Rating': row.review_rating,'Monteray Unit': row.unit,'Selling Price':row.sell_price,'Link': row.link,'Quantity of Reviews':str(row.quantity)},ignore_index=True)

    df.to_excel(filename,encoding='utf-8-sig',index=False)

    return send_file(filename)

@bp.route('/get_data')
def get_data():
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

    query = db.session.query().select_from(Asin).order_by(desc(Asin.id))
    params = request.args.to_dict()
    rowTable = DataTables(params, query, columns)

    # returns what is needed by DataTable
    return jsonify(rowTable.output_result())