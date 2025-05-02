from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired

class AddProductForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[DataRequired()])
    price = DecimalField('Цена', places=2, validators=[DataRequired()])
    category = SelectField('Категория', choices=[
        ('fresh', 'Свежий воздух'),
        ('mountain', 'Горный воздух'),
        ('forest', 'Лесной воздух'),
        ('sea', 'Морской воздух')
    ], validators=[DataRequired()])
    image = StringField('URL изображения', validators=[DataRequired()])
    submit = SubmitField('Добавить продукт')