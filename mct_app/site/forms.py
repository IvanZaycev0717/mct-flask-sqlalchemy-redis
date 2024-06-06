from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, ValidationError
from wtforms.validators import DataRequired, Optional
from flask_login import current_user

class QuestionForm(FlaskForm):
    anon_name = StringField(
        'Ваше имя',
        render_kw={"placeholder": "Введите ваше имя"},
        validators=[])
    body = TextAreaField(
        'Ваш вопрос',
        render_kw={"placeholder": "Введите текст вопроса"},
        validators=[DataRequired(message='Требуется ввести текст вопроса')])
    
    def validate_anon_name(self, anon_name):
        if not current_user.is_authenticated:
            if not self.anon_name.data:
                raise ValidationError('Требуется ввести имя')
        return True

class AnswerForm(FlaskForm):
    pass