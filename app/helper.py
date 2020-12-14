import re
import sys
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import datetime
from werkzeug.exceptions import HTTPException
from flask import jsonify
from app import db

def crawler_result(site_url, asin):
    url = 'https://'+site_url+'/dp/'+asin
    res = {}

    headersf={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}

    try:
        req = requests.get(url,headers=headersf)
        if req.status_code == 200:
            s=BeautifulSoup(req.content,features="lxml")

            quantr=""
            try:
                quantity_reviews=s.select("#acrCustomerReviewText.a-size-base")[0].get_text().strip()
                quantity_reviews=quantity_reviews.replace("ratings","")
                quantity_reviews = re.findall("(\d+(?:,d+)*)", quantity_reviews)

                for x in range(len(quantity_reviews),0,-1):
                    quantr=str(quantity_reviews[x-1])+quantr
            except IndexError:
                quantr='N/A'

            try:
                review=s.select("#averageCustomerReviews")[0].get_text().strip()
                review=str(review)
                r=review.split()
                review=r[0]
                if(len(review)>4):
                    review=review[-3:]
            except IndexError:
                review='N/A'

            if(review=='N/A'):
                try:
                    price=s.select("#acr-average-stars-rating-text")[0].get_text().strip()
                    if("-" in str(price)):
                        a=str(price).split("-")
                        f=a[0]
                        g=a[1]
                        price=f[1:]+"-"+g[2:]
                        memontary_unit=f[0:1]
                        memontary_unit=g[0:1]
                    elif (" " in str(price)):
                        a=str(price).split()
                        price=a[0]
                        memontary_unit=a[1]
                    else:
                        g=str(price)
                        price=price[1:]
                        memontary_unit=g[0:1]
                except IndexError:
                    price='N/A'
                    memontary_unit='N/A'

            try:
                price=s.select("#priceblock_ourprice")[0].get_text().strip()
                #print(price, '>>>>>>>>>>>>>>>>>>>>>>')

                if("-" in str(price)):
                    a=str(price).split("-")
                    f=a[0]
                    g=a[1]
                    price=f[1:]+"-"+g[2:]
                    memontary_unit=f[0:1]
                    memontary_unit=f[0:1]
                #elif ("," in str(price)):
                    #price=price[1:]
                    #memontary_unit=g[0:1]
                elif("€" in str(price)):
                    b = str(price).split("€")
                    c = [x.strip() for x in b if x.strip()]
                    price=c[0]
                    memontary_unit="€"
                else:
                    g=str(price)
                    price=price[1:]
                    memontary_unit=g[0:1]
            except IndexError:
                price='N/A'
                memontary_unit='N/A'

            if price=='N/A':
                try:
                    price=s.select("#priceblock_saleprice")[0].get_text().strip()
                    if("-" in str(price)):
                        a=str(price).split("-")
                        f=a[0]
                        g=a[1]
                        price=f[1:]+"-"+g[2:]
                        memontary_unit=f[0:1]
                        memontary_unit=g[0:1]
                    elif("€" in str(price)):
                        b = str(price).split("€")
                        c = [x.strip() for x in b if x.strip()]
                        price=c[0]
                        memontary_unit="€"
                    else:
                        g=str(price)
                        price=price[1:]
                        memontary_unit=g[0:1]
                except IndexError:
                    price='N/A'
                    memontary_unit='N/A'

            if price=='N/A':
                try:
                    price=s.select("#priceblock_dealprice")[0].get_text().strip()
                    if("-" in str(price)):
                        a=str(price).split("-")
                        f=a[0]
                        g=a[1]
                        price=f[1:]+"-"+g[2:]
                        memontary_unit=f[0:1]
                        memontary_unit=g[0:1]
                    elif("€" in str(price)):
                        b = str(price).split("€")
                        c = [x.strip() for x in b if x.strip()]
                        price=c[0]
                        memontary_unit="€"
                    else:
                        g=str(price)
                        price=price[1:]
                        memontary_unit=g[0:1]
                except IndexError:
                    price='N/A'
                    memontary_unit='N/A'

            if review == 'N/A' and memontary_unit == 'N/A' and quantr == 'N/A' and price == 'N/A':
                res = {
                'status': 'error',
                'site_url': site_url,
                'asin': asin,
                'review': review,
                'unit': memontary_unit,
                'quantity': quantr,
                'price': price,
                'link': url,
                'description': 'The cralwer has not gotten the correct data.'
            }
            else:
                res = {
                    'status': 'success',
                    'site_url': site_url,
                    'asin': asin,
                    'review': review,
                    'unit': memontary_unit,
                    'quantity': quantr,
                    'price': price,
                    'link': url,
                    'description': ''
                }
        else:
            res = {
                'status':  str(req.status_code) + ' Error code',
                'site_url': site_url,
                'asin': asin,
                'review': '',
                'unit': '',
                'quantity': '',
                'price': '',
                'link': url,
                'description': req.reason
            }
    except:
        res = {
                'status':  'Failed',
                'site_url': site_url,
                'asin': asin,
                'review': '',
                'unit': '',
                'quantity': '',
                'price': '',
                'link': url,
                'description': 'Currently unavailable.'
            }
    return res

def to_dict(row):
    if row is None:
        return None

    rtn_dict = dict()
    keys = row.__table__.columns.keys()
    for key in keys:
        rtn_dict[key] = getattr(row, key)
    return rtn_dict

def dt_to_str(date, fma='%Y-%m-%d'):
    return datetime.strftime(fma)

def max_value(price):
    if price is None or price == 'N/A' or price == '':
        return 'N/A'

    price = str(price)
    if price.find('-') > -1:
        price_ranges = str(price).split("-")
        price = price_ranges[1]
    elif price.find('~') > -1:
        price_ranges = str(price.split("~"))
        price = price_ranges[1]

    price = price.replace(',','')
    return float(price)

def max_review(price):
    if price is None or price == 'N/A' or price == '':
        return 'N/A'

    price = str(price)
    if price.find('-') > -1:
        price_ranges = str(price).split("-")
        price = price_ranges[1]
    elif price.find('~') > -1:
        price_ranges = str(price.split("~"))
        price = price_ranges[1]

    price = price.replace(',','.')
    return float(price)


def create_graph_data(result):
    price_data = []
    review_data = []
    quantity_data = []
    labels = []

    for row in result:
        price = max_value(row['sell_price'])
        review = max_review(row['review_rating'])
        quantity = max_value(row['quantity'])
        date = row['created_at']

        if price == 'N/A' and review == 'N/A'and quantity == 'N/A':
            continue;

        if price == 'N/A':
            price = None
        else:
            price = float(price)

        if review == 'N/A':
            review = None
        else:
            review = float(review)

        if quantity == 'N/A':
            quantity = None
        else:
            quantity = float(quantity)

        price_data.append(price)
        review_data.append(review)
        quantity_data.append(quantity)
        labels.append(date)

    return {
        'price_data': price_data,
        'review_data': review_data,
        'quantity_data': quantity_data,
        'labels': labels
    }

def get_by_time(_json):
    start_date = _json['start']
    end_date = _json['end']
    asin = _json['asin']
    site = _json['site']

    result = db.session.execute('SELECT asin, sell_price, review_rating, quantity, DATE_FORMAT(created_at, "%Y-%m-%d %H:%i:%s") as created_at FROM asins WHERE status="success" AND created_at >= :start_date AND created_at <= :end_date AND asin = :asin AND site_url = :site', {
            'start_date': start_date,
            'end_date': end_date,
            'asin': asin,
            'site': site
        })

    return create_graph_data(result)

def get_by_date(_json):
    start_date = _json['start']
    end_date = _json['end']
    asin = _json['asin']
    site = _json['site']

    sql = 'SELECT id, ASIN, sell_price, quantity, unit, review_rating, DATE_FORMAT(created_at, "%Y-%m-%d") as created_at '\
            'FROM asins '\
            'WHERE id IN '\
            '( '\
                'SELECT MAX(id) '\
                'FROM asins '\
                'WHERE asin=:asin '\
                'AND status="success" '\
                'AND site_url=:site '\
                'AND created_at >= :start_date AND created_at <= :end_date '\
                'GROUP BY DATE_FORMAT(created_at, "%Y-%m-%d") '\
            ') '\

    result = db.session.execute(sql, {
            'start_date': start_date,
            'end_date': end_date,
            'asin': asin,
            'site': site
        })

    return create_graph_data(result)

def get_by_week(_json):
    start_date = _json['start']
    end_date = _json['end']
    asin = _json['asin']
    site = _json['site']

    sql = 'SELECT id, ASIN, sell_price, quantity, unit, review_rating, CONCAT(DATE_FORMAT(created_at,"%m"),"月",FLOOR((DAYOFMONTH(created_at)-1)/7)+1, "周") as created_at '\
            'FROM asins '\
            'WHERE id IN '\
            '( '\
                'SELECT MAX(id) '\
                'FROM asins '\
                'WHERE asin=:asin '\
                'AND site_url=:site '\
                'AND status="success" '\
                'AND created_at >= :start_date AND created_at <= :end_date '\
                'GROUP BY WEEK(created_at) '\
            ') '\

    result = db.session.execute(sql, {
            'start_date': start_date,
            'end_date': end_date,
            'asin': asin,
            'site': site
        })

    return create_graph_data(result)
    return result

def get_ready_excel(_json):
    start_date = _json['start']
    end_date = _json['end']
    asin = _json['asin']
    site = _json['site']

    sql = 'SELECT id, ASIN, sell_price, quantity, unit, review_rating, DATE_FORMAT(created_at, "%Y-%m-%d %H:%i:%s") as created_at '\
            'FROM asins '\
            'WHERE id IN '\
            '( '\
                'SELECT MAX(id) '\
                'FROM asins '\
                'WHERE ASIN=:asin '\
                'AND site_url=:site '\
                'AND status="success" '\
                'AND created_at >= :start_date AND created_at <= :end_date '\
                'GROUP BY DATE_FORMAT(created_at, "%Y-%m-%d") '\
            ') '\

    result = db.session.execute(sql, {
            'start_date': start_date,
            'end_date': end_date,
            'asin': asin,
            'site': site
        })
    current_price = 0
    current_review = 0

    excel_data = []
    for row in result:
        price = max_value(row['sell_price'])
        review = max_value(row['review_rating'])
        quantity = max_value(row['quantity'])
        date = row['created_at']

        if price == 'N/A' and review == 'N/A'and quantity == 'N/A':
            continue;

        if price == 'N/A':
            price = current_price
        else:
            price = float(price)

        if review == 'N/A':
            review = current_review
        else:
            review = float(review)

        if current_price == 0:
            diff_price = ''
        else:
            diff_price = float(price - current_price)
            if diff_price > 0:
                diff_price = '+' + str(diff_price)

        if current_review == 0:
            diff_review = ''
        else:
            diff_review = float(review - current_review)
            if diff_review > 0:
                diff_review = '+' + str("{:.2f}".format(diff_review))

        item = {
            'asin': asin,
            'price': row['sell_price'],
            'diff_price': diff_price,
            'review': row['review_rating'],
            'diff_review': diff_review,
            'quantity': row['quantity'],
            'date': date
        }
        excel_data.append(item)
        current_price = price
        current_review = review

    return excel_data

def get_by_month(_json):
    start_date = _json['start']
    end_date = _json['end']
    asin = _json['asin']
    site = _json['site']
    sql = 'SELECT id, ASIN, sell_price, quantity, unit, review_rating, DATE_FORMAT(created_at, "%Y-%m") as created_at '\
            'FROM asins '\
            'WHERE id IN '\
            '( '\
                'SELECT MAX(id) '\
                'FROM asins '\
                'WHERE ASIN=:asin '\
                'AND site_url=:site '\
                'AND status="success" '\
                'AND created_at >= :start_date AND created_at <= :end_date '\
                'GROUP BY DATE_FORMAT(created_at, "%Y-%m") '\
            ') '\

    result = db.session.execute(sql, {
            'start_date': start_date,
            'end_date': end_date,
            'asin': asin,
            'site': site
        })

    return create_graph_data(result)
