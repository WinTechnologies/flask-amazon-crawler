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

    return
