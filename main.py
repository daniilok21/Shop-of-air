from datetime import datetime
from flask import Flask, render_template, redirect, request, abort, url_for, Response, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import delete, select
from data import db_session
from data.orders import Order
from data.products import Product
from data.users import User
from forms.payment import PaymentForm
from forms.products import ProductForm
from forms.user import RegisterForm, LoginForm
from werkzeug.utils import secure_filename
import os
import logging
import json
from flask_restful import Api
from api.products import ProductsResource, ProductsListResource
from api.orders import OrdersResource, OrdersListResource

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

api = Api(app)

api.add_resource(ProductsListResource, '/api/products')
api.add_resource(ProductsResource, '/api/products/<int:product_id>')

api.add_resource(OrdersListResource, '/api/orders')
api.add_resource(OrdersResource, '/api/orders/<int:order_id>')

login_manager = LoginManager()
login_manager.init_app(app)

logging.basicConfig(
    filename='example.log',
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', form=form, message="Пароли не совпадают")

        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', form=form, message="Пользователь уже существует")

        user = User(
            surname=form.surname.data,
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/')
def index():
    db_sess = db_session.create_session()
    products = db_sess.query(Product).filter(Product.is_available == True).all()
    return render_template("index.html", products=products)


@app.route('/product/<int:id>')
def product(id):
    db_sess = db_session.create_session()
    product = db_sess.get(Product, id)
    if not product:
        abort(404)
    return render_template("product.html", product=product)


@app.route('/buy/<int:product_id>', methods=['POST'])
@login_required
def buy(product_id):
    db_sess = db_session.create_session()
    product = db_sess.get(Product, product_id)
    quantity = int(request.form.get('quantity', 1))

    if product.quantity < quantity:
        return "Недостаточно товара"

    total = product.price * quantity

    if current_user.balance < total:
        return "Недостаточно средств"

    current_user.balance -= total
    product.quantity -= quantity

    order = Order(
        user_id=current_user.id,
        product_id=product.id,
        quantity=quantity,
        total=total
    )
    db_sess.add(order)
    db_sess.commit()

    return redirect(url_for('index'))


@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        abort(403)

    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    products = db_sess.query(Product).all()

    return render_template('admin_panel.html',
                           users=users,
                           products=products)


@app.route('/orders')
@login_required
def orders():
    db_sess = db_session.create_session()
    try:
        orders = db_sess.query(Order).filter(
            Order.user_id == current_user.id
        ).order_by(Order.created_at.desc()).all()

        db_sess.close()
        return render_template("orders.html", orders=orders)

    except Exception as e:
        logging.error(f"Ошибка при получении заказов: {str(e)}")
        abort(500)
        db_sess.close()


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@app.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        if amount <= 0:
            logging.info("Сумма должна быть больше нуля")
        else:
            current_user.balance += amount
            db_sess = db_session.create_session()
            db_sess.merge(current_user)
            db_sess.commit()
            logging.info(f"Пополнение баланса пользователем {current_user.email} на {amount} р.")
            return redirect('/profile')

    return render_template('payment.html')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        abort(403)

    form = ProductForm()
    form.category.choices = [('air', 'Воздух'), ('other', 'Другое')]

    if form.validate_on_submit():
        db_sess = db_session.create_session()

        image_path = None
        if form.image.data:
            file = form.image.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f'uploads/{filename}'

        product = Product(
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            quantity=form.quantity.data,
            image_url=image_path,
            category=form.category.data
        )

        db_sess.add(product)
        db_sess.commit()
        return redirect(url_for('admin_panel'))

    return render_template('add_product.html', form=form)


@app.route('/admin/product/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    if not current_user.is_admin:
        abort(403)

    db_sess = db_session.create_session()
    product = db_sess.get(Product, id)
    if not product:
        db_sess.close()
        abort(404)

    form = ProductForm(obj=product)
    form.category.choices = [('air', 'Воздух'), ('other', 'Другое')]

    if form.validate_on_submit():
        try:
            old_image = product.image_url
            form.populate_obj(product)

            if form.image.data:
                file = form.image.data
                if file and allowed_file(file.filename):
                    if old_image:
                        try:
                            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_image.split('/')[-1]))
                        except Exception as e:
                            logging.error(f"Ошибка удаления изображения: {str(e)}")
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    product.image_url = f'uploads/{filename}'

            db_sess.commit()
            db_sess.close()
            return redirect(url_for('admin_panel'))

        except Exception as e:
            db_sess.rollback()
            logging.error(f"Ошибка сохранения товара {id}: {str(e)}")
            db_sess.close()

    return render_template('edit_product.html', form=form, product=product)


@app.route('/admin/product/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    if not current_user.is_admin:
        abort(403)

    db_sess = db_session.create_session()
    try:
        product = db_sess.get(Product, id)
        if not product:
            logging.warning(f"Удаления несуществующего товара {id}")
            return redirect(url_for('admin_panel'))
        db_sess.execute(delete(Order).where(Order.product_id == id))
        db_sess.delete(product)
        db_sess.commit()
        logging.info(f"Товар {product.title} {id} удален")
        db_sess.close()

    except Exception as e:
        db_sess.rollback()
        logging.error(f"Ошибка при удалении товара {str(e)} {id}")
        db_sess.close()

    return redirect(url_for('admin_panel'))


@app.route('/cart')
@login_required
def cart():
    db_sess = db_session.create_session()

    checkout_success = request.args.get('checkout_success') == 'True'

    orders = db_sess.query(Order).filter(Order.user_id == current_user.id).all()

    cart_items = []
    total_quantity = 0
    total_amount = 0

    for order in orders:
        product = db_sess.get(Product, order.product_id)
        if product:
            cart_items.append({
                'product': product,
                'quantity': order.quantity
            })
            total_quantity += order.quantity
            total_amount += order.quantity * product.price

    db_sess.close()

    return render_template('cart.html',
                           cart_items=cart_items,
                           total_quantity=total_quantity,
                           total_amount=total_amount,
                           checkout_success=checkout_success)


@app.route('/cart/update', methods=['POST'])
@login_required
def update_cart_item():
    product_id = int(request.form.get('product_id'))
    action = request.form.get('action')
    quantity = int(request.form.get('quantity', 1))

    db_sess = db_session.create_session()
    try:
        order = db_sess.query(Order).filter(
            Order.user_id == current_user.id,
            Order.product_id == product_id
        ).first()

        if not order:
            db_sess.close()
            abort(404)

        product = db_sess.get(Product, product_id)

        # Обрабатываем действие (увеличение/уменьшение)
        if action == 'increase':
            new_quantity = quantity + 1
        elif action == 'decrease':
            new_quantity = quantity - 1
        else:
            new_quantity = quantity

        # Проверяем доступное количество
        if new_quantity < 1 or (product.quantity < new_quantity):
            db_sess.close()
            return redirect(url_for('cart'))

        order.quantity = new_quantity
        order.total = product.price * new_quantity
        db_sess.commit()

    except Exception as e:
        db_sess.rollback()
        logging.error(f"Ошибка обновления корзины: {str(e)}")

    db_sess.close()

    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_cart_item(product_id):
    db_sess = db_session.create_session()
    try:
        order = db_sess.query(Order).filter(
            Order.user_id == current_user.id,
            Order.product_id == product_id
        ).first()

        if order:
            db_sess.delete(order)
            db_sess.commit()
    except Exception as e:
        db_sess.rollback()
        logging.error(f"Ошибка удаления из корзины: {str(e)}")

    db_sess.close()
    return redirect(url_for('cart'))


@app.route('/cart/checkout', methods=['POST'])
@login_required
def checkout():
    db_sess = db_session.create_session()
    try:
        cart_items = db_sess.query(Order).filter(Order.user_id == current_user.id).all()

        if not cart_items:
            logging.info('Ваша корзина пуста')
            return redirect(url_for('cart'))

        total_amount = sum(item.total for item in cart_items)

        if current_user.balance < total_amount:
            logging.error('Недостаточно средств на балансе')
            return redirect(url_for('cart'))

        for item in cart_items:
            product = db_sess.get(Product, item.product_id)
            if not product or product.quantity < item.quantity:
                logging.error(f'Товар "{product.title if product else "Unknown"}" недоступен в нужном количестве')
                return redirect(url_for('cart'))

        current_user.balance -= total_amount

        for item in cart_items:
            product = db_sess.get(Product, item.product_id)
            product.quantity -= item.quantity
            item.status = 'completed'
            item.created_at = datetime.now()

        db_sess.commit()
        db_sess.close()
        return redirect(url_for('cart', checkout_success=True))

    except Exception as e:
        db_sess.rollback()
        logging.error(f"Ошибка оформления заказа: {str(e)}")
        db_sess.close()
        return redirect(url_for('cart'))


def init_all():
    db_sess = db_session.create_session()
    if not db_sess.query(User).filter(User.email == "admin@example.com").first():
        admin = User(
            surname="Admin",
            name="Admin",
            email="admin@example.com",
            is_admin=True
        )

        admin.set_password("admin123")
        db_sess.add(admin)
        db_sess.commit()
        logging.info("Создан администратор: admin@example.com / admin123")

    db_sess.close()


if __name__ == '__main__':
    db_session.global_init("db/shop.db")
    db_sess = db_session.create_session()

    init_all()

    app.run(port=5000, debug=True)
