from flask import jsonify, request
from flask_restful import Resource, abort
from flask_httpauth import HTTPBasicAuth
from data import db_session
from data.products import Product
from data.users import User

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    session = db_session.create_session()
    user = session.query(User).filter(User.email == username).first()
    if user and user.check_password(password):
        return user
    return None


def abort_if_product_not_found(product_id):
    session = db_session.create_session()
    product = session.query(Product).get(product_id)
    if not product:
        abort(404, message=f"Product {product_id} not found")
    return product


class ProductsResource(Resource):
    def get(self, product_id):
        product = abort_if_product_not_found(product_id)
        return jsonify({
            'product': product.to_dict()
        })

    @auth.login_required
    def delete(self, product_id):
        if not auth.current_user().is_admin:
            abort(403, message="Admin access required")

        product = abort_if_product_not_found(product_id)
        session = db_session.create_session()
        session.delete(product)
        session.commit()
        return jsonify({'success': 'OK'})


class ProductsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        products = session.query(Product).filter(Product.is_available == True).all()
        return jsonify({
            'products': [product.to_dict() for product in products]
        })

    @auth.login_required
    def post(self):
        try:
            if not auth.current_user().is_admin:
                return {"message": "Admin access required"}, 403

            required_fields = ['title', 'price', 'quantity', 'category']
            if not all(field in request.json for field in required_fields):
                return {"message": f"Missing required fields: {required_fields}"}, 400

            db_sess = db_session.create_session()
            product = Product(
                title=request.json['title'],
                price=request.json['price'],
                quantity=request.json['quantity'],
                category=request.json['category'],
                description=request.json.get('description', ''),
                image_url=request.json.get('image_url', None),
                is_available=request.json.get('is_available', True)
            )
            db_sess.add(product)
            db_sess.commit()

            return {"id": product.id}, 201

        except Exception as e:
            db_sess.rollback()
            return {"message": str(e)}, 500
        finally:
            db_sess.close()
