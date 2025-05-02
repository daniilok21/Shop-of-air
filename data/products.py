from data.db_session import SqlAlchemyBase
import sqlalchemy as sa
from sqlalchemy import orm


class Product(SqlAlchemyBase):
    __tablename__ = 'products'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    title = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text)
    price = sa.Column(sa.Float, nullable=False)
    quantity = sa.Column(sa.Integer, default=0)
    image_url = sa.Column(sa.String)
    category = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime, default=sa.func.now())
    is_available = sa.Column(sa.Boolean, default=True)