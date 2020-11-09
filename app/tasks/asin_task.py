from app import db
from app import celery

from app.helper import crawler_result
from app.models.asin import Asin

@celery.task()
def save_data(domain, asin_symbol):
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
    new_pk_id = new_asin.id
    asin = Asin.query.filter(Asin.id == new_pk_id).first()
    try:
        result = crawler_result(domain, asin_symbol)
        asin.review_rating = result.get('review')
        asin.quantity = result.get('quantity')
        asin.unit = result.get('unit')
        asin.sell_price = result.get('price')
        asin.status = result.get('status')
        asin.description = result.get('description')

        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()

        asin.review_rating = 'N/A'
        asin.quantity = 'N/A'
        asin.unit = 'N/A'
        asin.sell_price = 'N/A'
        asin.status = 'Failed'
        asin.description = 'Currently unavailable.'
        db.session.flush()
        db.session.commit()
    finally:
        db.session.close()

    return
