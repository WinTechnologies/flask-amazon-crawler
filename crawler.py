import os
from flask import Flask, render_template, request
from flask_mysqldb import MySQL
from werkzeug import secure_filename

import pandas as pd
import numpy as np

import redis
from rq import Queue
from rq.job import Job
from worker import conn

from bs4 import BeautifulSoup
import requests
import re
import sys

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DATABASE'] = 'asin'
mysql = MySQL(app)

app_root = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    target = os.path.join(app_root, 'uploads')
    if not os.path.isdir(target):
        os.mkdir(target)

    if request.method == 'POST':
        f=request.files['input']
        file_name = f.filename
        destination = os.path.join(target, file_name)
        f.save(destination)

        i=0
        with open(destination, 'r') as file:
            lines = file.readlines()
        for line in lines:
            cc=line.split()
            i=i+1
            #print("ASIN: "+cc[1]+" ,Review_Rating "+review+" ,Price "+memontary_unit+price+" Quantity Reviews "+quantr)
        return target


if __name__ == '__main__':
    app.run(debug = True)