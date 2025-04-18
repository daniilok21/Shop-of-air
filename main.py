from flask import Flask, render_template, redirect, request, abort, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from data import db_session
from data.orders import Order
from data.products import Product
from data.users import User
from forms.payment import PaymentForm
from forms.products import ProductForm
from forms.user import RegisterForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        print(6213215)
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
    product = db_sess.query(Product).get(id)
    return render_template("product.html", product=product)


@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not current_user.is_admin:
        abort(403)
    form = ProductForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        product = Product(
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            quantity=form.quantity.data,
            image_url=form.image_url.data
        )
        db_sess.add(product)
        db_sess.commit()
        return redirect('/')
    return render_template('edit_product.html', form=form)


@app.route('/buy/<int:product_id>', methods=['POST'])
@login_required
def buy(product_id):
    db_sess = db_session.create_session()
    product = db_sess.query(Product).get(product_id)
    quantity = int(request.form.get('quantity', 1))

    if product.quantity < quantity:
        return "Недостаточно товара"

    total = product.price * quantity

    if current_user.balance < total:
        return "Недостаточно средств"

    # Обновляем баланс и количество
    current_user.balance -= total
    product.quantity -= quantity

    # Создаем запись о покупке
    order = Order(
        user_id=current_user.id,
        product_id=product.id,
        quantity=quantity,
        total=total
    )
    db_sess.add(order)
    db_sess.commit()

    return redirect('/orders')


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
    orders = db_sess.query(Order).filter(Order.user_id == current_user.id).all()
    return render_template("orders.html", orders=orders)


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
            print("Сумма должна быть больше нуля")
        else:
            current_user.balance += amount
            db_sess = db_session.create_session()
            db_sess.merge(current_user)
            db_sess.commit()
            print(f"Баланс пополнен на {amount} ₽")
            return redirect('/profile')

    return render_template('payment.html')


if __name__ == '__main__':
    db_session.global_init("db/shop.db")
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
        print("Создан администратор: admin@example.com / admin123")

    app.run(port=5000, debug=True)