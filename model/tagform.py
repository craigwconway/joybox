from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired


class TagForm(FlaskForm):
    id = HiddenField('id')
    name = StringField('Name', validators=[DataRequired()])
    link = StringField('YouTube Link', validators=[DataRequired()])
    submit = SubmitField('Save')
