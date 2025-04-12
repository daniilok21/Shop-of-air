import datetime
import sqlalchemy
from data.db_session import SqlAlchemyBase


class Order(SqlAlchemyBase):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    product_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('products.id'))
    quantity = sqlalchemy.Column(sqlalchemy.Integer)
    total = sqlalchemy.Column(sqlalchemy.Float)
    date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)