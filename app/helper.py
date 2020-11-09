import re
import sys
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import datetime
from werkzeug.exceptions import HTTPException

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
                print('price: ', price, '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
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