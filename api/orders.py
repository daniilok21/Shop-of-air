from flask import jsonify
from flask_restful import Resource, abort
from data import db_session
from data.orders import Order
from data.products import Product
from flask_login import current_user
from api.products import auth


class OrdersResource(Resource):
    def get(self, order_id):
        if not current_user.is_authenticated:
            abort(401, message="Authentication required")

        db_sess = db_session.create_session()
        order = db_sess.query(Order).get(order_id)

        if not order or (order.user_id != current_user.id and not current_user.is_admin):
            abort(404, message=f"Order {order_id} not found")

        product = db_sess.query(Product).get(order.product_id)
        return jsonify({
            'order': {
                'id': order.id,
                'product_title': product.title,
                'quantity': order.quantity,
                'total': order.total,
                'date': order.date.isoformat()
            }
        })


class OrdersListResource(Resource):
    @auth.login_required
    def get(self):
        user = auth.current_user()
        db_sess = db_session.create_session()
        if user.is_admin:
            orders = db_sess.query(Order).all()
        else:
            orders = db_sess.query(Order).filter(Order.user_id == user.id).all()

        result = []
        for order in orders:
            product = db_sess.query(Product).get(order.product_id)
            result.append({
                'id': order.id,
                'product_title': product.title,
                'quantity': order.quantity,
                'total': order.total,
                'date': order.date.isoformat()
            })

        return jsonify({'orders': result})