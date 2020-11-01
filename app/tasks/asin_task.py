from app import db
from app import celery

from app.helper import crawler_result
from app.models.asin import Asin

@celery.task()
def save_data(domain, asin_symbol):
    result = crawler_result(domain, asin_symbol)
    try:
        yield
        new_asin = Asin(
            site_url=result.get('site_url'),
            asin=result.get('asin'),
            review_rating=result.get('review'),
            quantity=result.get('quantity'),
            unit=result.get('unit'),
            sell_price=result.get('price'),
            link=result.get('link'),
            status='success',
            description='no issue'
        )
        db.session.add(new_asin)
        db.session.commit()
    except Exception:
        db.session.rallback()
        raise
        new_asin = Asin(
            site_url=domain,
            asin=asin_symbol,
            review_rating='',
            quantity='',
            unit='',
            sell_price='',
            link='https://'+domain+'/dp/'+asin_symbol,
            status='error',
            description=result
        )
        db.session.add(new_asin)
        db.session.commit()

    return
