from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class PaymentForm(FlaskForm):
    amount = FloatField('Сумма', validators=[
        DataRequired(),
        NumberRange(min=0.1, max=10000)
    ])
    submit = SubmitField('Пополнить')