from __future__ import unicode_literals
import json
import os.path
import random
import re
import unicodedata

import vlc
import youtube_dl

from flask import Flask, render_template, redirect, request, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.simple import HiddenField
from wtforms.validators import DataRequired

import RPi.GPIO as GPIO
from pn532 import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'x3HqRBL-9GBo._VmJHY-'
Bootstrap(app)  # Flask-Bootstrap requires this line


class TagForm(FlaskForm):
    id = HiddenField('id')
    name = StringField('Name', validators=[DataRequired()])
    link = StringField('YouTube Link', validators=[DataRequired()])
    submit = SubmitField('Save')


player = vlc.MediaListPlayer()
playing = False
reading = False
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
        'outtmpl': '%s.%s' % (filename, '%(etx)s'),
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


tags = get_data()["tags"]

try:
    pn532 = PN532_SPI(debug=False, reset=20, cs=4)
    ic, ver, rev, support = pn532.get_firmware_version()
    print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))
    pn532.SAM_configuration()
    print('Waiting for RFID/NFC card...')
    while reading:
        uid = pn532.read_passive_target(timeout=0.5)
        if uid is None:
            player.stop()
            playing = False
            continue
        print('Found uid.hex():', uid.hex())
        if not playing:
            try:
                print("Playing: ", tags[uid.hex()]["link"])
                player.set_media_list(vlc.MediaList(
                    [slugify(tags[uid.hex()]["link"])+".mp3"]))
                player.play()
                playing = True
            except Exception as x:
                print("No mapping: ", uid.hex())
                # TODO play default

except Exception as e:
    print(e)


def get_tag_id():
    print("Getting tag from reader...")
    try:
        uid = pn532.read_passive_target(timeout=0.5)
        return uid.hex()
    except Exception as e:
        print(e)
        return random.getrandbits(8)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', tags=get_data()["tags"])


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    args = request.args
    data = get_data()
    form = TagForm()
    tags = data["tags"]
    tag = ""
    if "tag" in args and request.method == "GET":
        tag = args["tag"]
        form.id.data = tag
        form.name.data = tags[tag]["name"]
        form.link.data = tags[tag]["link"]
    if "delete" in args:
        tags.pop(tag, None)
        data["tags"] = tags
        write_data(data)
        return redirect("/")
    if form.validate_on_submit():
        tag = form.id.data
        if not tag:
            tag = get_tag_id()
        download(form.link.data)
        tags[tag] = {"name": form.name.data, "link": form.link.data}
        data["tags"] = tags
        write_data(data)
        return redirect("/")
    return render_template('edit.html', form=form, tag=tag)
