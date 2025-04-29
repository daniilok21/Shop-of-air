import sqlalchemy
from sqlalchemy import orm
from data.db_session import SqlAlchemyBase


class Product(SqlAlchemyBase):
    __tablename__ = 'products'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.Text)
    price = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    quantity = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    image_url = sqlalchemy.Column(sqlalchemy.String)
    is_available = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
