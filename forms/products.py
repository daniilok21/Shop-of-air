from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class ProductForm(FlaskForm):
    title = StringField('Название товара', validators=[DataRequired()])
    description = TextAreaField('Описание')
    price = FloatField('Цена', validators=[DataRequired(), NumberRange(min=0.01)])
    quantity = IntegerField('Количество', validators=[NumberRange(min=0)])
    image = FileField('Изображение товара', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')
    ])
    category = SelectField('Категория', choices=[
        ('air', 'Воздух'),
        ('other', 'Другое')
    ], validators=[DataRequired()])
    submit = SubmitField('Добавить товар')