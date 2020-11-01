import os
import requests
import re
import sys

from flask import Flask, render_template, request, Blueprint, jsonify, redirect
from sqlalchemy import desc

from app import db
from app.models.asin import Asin
from app.tasks.asin_task import save_data
from app.forms.search import SearchForm

from datatables import ColumnDT, DataTables


host_url = 'http://127.0.0.1:5000'
bp = Blueprint("all", __name__)
app_root = os.path.dirname(os.path.abspath(__file__))

@bp.route("/")
def index():
    search_form = SearchForm()
    return render_template('index.html', host_url=host_url, form=search_form)

@bp.route('/uploader', methods=['GET', 'POST'])
def uploader():
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
        for line in lines:
            cc=line.split()
            save_data.delay(cc[0], cc[1])

        return 'The input file has been uploaded successfully, our system has started to insert the crawler result into the table under background already.'
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