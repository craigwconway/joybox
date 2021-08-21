from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired


import json

import RPi.GPIO as GPIO
from pn532 import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'x3HqRBL-9GBo._VmJHY-'

# Flask-Bootstrap requires this line
Bootstrap(app)


class TagForm(FlaskForm):
    id = HiddenField('id', validators=[
                     DataRequired()], default="<Tag Not Found>")
    name = StringField('Name', validators=[DataRequired()])
    link = StringField('YouTube Link', validators=[DataRequired()])
    submit = SubmitField('Submit')


file_name = "data.json"


def get_data():
    with open(file_name) as f:
        data = json.load(f)
        f.close()
        return data


def write_data(data):
    with open(file_name, "w") as f:
        json.dump(data, f)
        f.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', message=get_data())


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    data = get_data()

    form = TagForm()
    if form.validate_on_submit():
        id = get_tag_id()
        data["tags"].append({
            "id": id,
            "name": form.name.data,
            "link": form.link.data,
        })
        write_data(data)

    return render_template('edit.html', form=form, message=data)


def get_tag_id():
    try:
        pn532 = PN532_SPI(debug=False, reset=20, cs=4)
        ic, ver, rev, support = pn532.get_firmware_version()
        print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))
        pn532.SAM_configuration()
        print('Waiting for RFID/NFC card...')
        found = False
        while not found:
            # Check if a card is available to read
            uid = pn532.read_passive_target(timeout=0.5)
            print('.', end="")
            # Try again if no card is available.
            if uid:
                found = True
                print('Found uid.hex():', uid.hex())
                return uid.hex()
    except Exception as e:
        print(e)
        return "<Tag Not Found>"
    finally:
        GPIO.cleanup()
