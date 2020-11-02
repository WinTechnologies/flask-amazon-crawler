from app import db
from app import celery

from app.helper import crawler_result
from app.models.asin import Asin

@celery.task()
def save_data(domain, asin_symbol):
    result = crawler_result(domain, asin_symbol)

    new_asin = Asin(
            site_url=result.get('site_url'),
            asin=result.get('asin'),
            review_rating=result.get('review'),
            quantity=result.get('quantity'),
            unit=result.get('unit'),
            sell_price=result.get('price'),
            link=result.get('link'),
            status=result.get('status'),
            description=result.get('description')
        )
    db.session.add(new_asin)
    db.session.commit()
    return
