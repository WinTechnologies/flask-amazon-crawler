from datetime import datetime
from app import db

class Asin(db.Model):
    __tablename__ = 'asins'

    id = db.Column(db.Integer, primary_key=True)
    site_url = db.Column(db.String(64))
    asin = db.Column(db.String(64))
    review_rating = db.Column(db.String(64))
    quantity = db.Column(db.String(64))
    unit = db.Column(db.String(64))
    sell_price = db.Column(db.String(64))
    link = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(64))
    description = db.Column(db.String(200))

    def __repr__(self):
        return '<Asin {}>'.format(self.link)
