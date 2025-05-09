from flask_httpauth import HTTPBasicAuth
from flask_login import current_user
from werkzeug.security import check_password_hash
from data.users import User
from data import db_session

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email, password):
    if current_user.is_authenticated:
        return True

    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.email == email).first()
    if user and user.check_password_hash(password):
        return True
    return False