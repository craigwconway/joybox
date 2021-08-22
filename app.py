from __future__ import unicode_literals
import unicodedata
import re
import os.path
import json

import youtube_dl
import vlc

from flask import Flask, render_template, redirect, request, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired

# import RPi.GPIO as GPIO
# from pn532 import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'x3HqRBL-9GBo._VmJHY-'
Bootstrap(app)  # Flask-Bootstrap requires this line


class TagForm(FlaskForm):
    id = HiddenField('id', validators=[
                     DataRequired()], default="DEFAULT")
    name = StringField('Name', validators=[DataRequired()])
    link = StringField('YouTube Link', validators=[DataRequired()])
    submit = SubmitField('Submit')


player = vlc.MediaListPlayer()
playing = False
reading = True
data_file = "data.json"


def get_data():
    with open(data_file) as f:
        data = json.load(f)
        f.close()
        return data


def write_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f)
        f.close()


def slugify(value, allow_unicode=False):
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode(
            'ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def download(video_url):
    filename = slugify(video_url)
    print('Exists: ', os.path.isfile(filename))
    ydl_opts = {
        'outtmpl': filename + '.mp3',
        'nocheckcertificate': True,
        'format': 'bestaudio/best',
        'keepvideo': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        r = ydl.download([video_url])


tag_map = get_data()["tags"]

# try:
#     pn532 = PN532_SPI(debug=False, reset=20, cs=4)
#     ic, ver, rev, support = pn532.get_firmware_version()
#     print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))
#     pn532.SAM_configuration()
#     print('Waiting for RFID/NFC card...')
#     while reading:
#         uid = pn532.read_passive_target(timeout=0.5)
#         if uid is None:
#             player.stop()
#             playing = False
#             continue
#         print('Found uid.hex():', uid.hex())
#         if not playing:
#             try:
#                 print("Playing: ", tag_map[uid.hex()])
#                 player.set_media_list(vlc.MediaList([slugify(tag_map[uid.hex()])]))
#                 player.play()
#                 playing = True
#             except Exception as x:
#                 print("No mapping: ", uid.hex())
#                 # TODO play default

# except Exception as e:
#     print(e)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', message=get_data()["tags"])


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    args = request.args
    data = get_data()
    form = TagForm()
    tags = data["tags"]
    if "tag" in args:
        tag = args["tag"]
        form.id.data = tag
        form.name.data = tags[tag]["name"]
        form.link.data = tags[tag]["link"]
    if form.validate_on_submit():
        id = get_tag_id()
        download(form.link.data)
        data["tags"][id] = {
            "name": form.name.data,
            "link": form.link.data,
        }
        write_data(data)
        return render_template('index.html', message=data["tags"])
    return render_template('edit.html', form=form, message="")


def get_tag_id():
    try:
        uid = pn532.read_passive_target(timeout=0.5)
        return uid.hex()
    except Exception as e:
        print(e)
        return "TAG_NOT_FOUND"
