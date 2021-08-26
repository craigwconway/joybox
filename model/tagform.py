from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, SubmitField, TextAreaField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired


class TagForm(FlaskForm):
    id = HiddenField('id')
    name = StringField('Name', validators=[DataRequired()])
    urls = TextAreaField('YouTube Links (1 per line)',
                         validators=[DataRequired()],
                         render_kw={
                             "rows": 11, "cols": 10
                         })
    shuffle = BooleanField('Shuffle')
    repeat = BooleanField('Repeat')
    submit = SubmitField('Save')
