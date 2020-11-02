import os
import requests
import re
import sys

from flask import Flask, render_template, request, Blueprint, jsonify, redirect, send_file
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
    return render_template('index.html', form=search_form, count=-1)

@bp.route('/uploader', methods=['GET', 'POST'])
def uploader():
    search_form = SearchForm()
    target = os.path.join(app_root, 'uploads')
    if not os.path.isdir(target):
        os.mkdir(target)

    if request.method == 'POST' and request.files['input']:
        f=request.files['input']
        file_name = f.filename
        destination = os.path.join(target, file_name)
        f.save(destination)

        with open(destination, 'r') as file:
            lines = file.readlines()
        count = 0

        for line in lines:
            cc=line.split()
            save_data.delay(cc[0], cc[1])
            count += 1

        return str(count) + ' crawlers are running in background, you can check them to refresh the page.' + ' <a href="/">back</a>'
    else:
        redirect('/')

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