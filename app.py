from __future__ import unicode_literals
import re
import unicodedata
import atexit
import json
import os.path
import random
import shutil
import threading

import vlc
import youtube_dl

from flask import Flask, render_template, redirect, request, url_for
from flask_bootstrap import Bootstrap

from model import *


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


POOL_TIME = .5  # Seconds
data_file = "data.json"
player = vlc.MediaListPlayer()
reader = Reader(player, get_data()["tags"])
data_map = {"current_tag": None}
t_lock = threading.Lock()
t_reader = threading.Thread()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'x3HqRBL-9GBo._VmJHY-'
    Bootstrap(app)  # Flask-Bootstrap requires this line

    def interrupt():
        global t_reader
        t_reader.cancel()

    def initReader():
        global data_map
        global t_reader
        with t_lock:
            try:
                reader.start()
            except:
                pass

        t_reader = threading.Timer(POOL_TIME, initReader, ())
        t_reader.start()

    def start():
        global t_reader
        t_reader = threading.Timer(POOL_TIME, initReader, ())
        t_reader.start()

    start()
    atexit.register(interrupt)
    return app


app = create_app()


def download(tag, url):
    if not url:
        return
    filename = "downloads/" + tag + "/" + slugify(url)
    if not os.path.isfile(filename+".mp3"):
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
            r = ydl.download([url])


def play_tag(tag):
    print("Playing: ", tag)
    playlist = ["downloads/" + tag + "/" + slugify(url) + ".mp3" for url in get_data()
                ["tags"][tag]["urls"]]
    print("PLAYLIST: ", playlist)
    player.set_media_list(vlc.MediaList(playlist))
    player.play()


@ app.route('/', methods=['GET'])
def index():
    return render_template('index.html', tags=get_data()["tags"])


@ app.route('/edit', methods=['GET', 'POST'])
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
        form.repeat.data = tags[tag]["repeat"]
        form.shuffle.data = tags[tag]["shuffle"]
        urls_text = ""
        for url in tags[tag]["urls"]:
            urls_text = urls_text + url + "\r\n"
        form.urls.data = urls_text
    if "delete" in args:
        tags.pop(tag, None)
        data["tags"] = tags
        write_data(data)
        shutil.rmtree("downloads/" + tag)
        return redirect("/")
    if form.validate_on_submit():
        tag = form.id.data
        if not tag:
            try:
                tag = reader.last_tag
            except:
                tag = random.getrandbits(8)
        urls = [url for url in form.urls.data.split("\r\n") if url != ""]
        for url in urls:
            download(tag, url)
        tags[tag] = {"name": form.name.data,
                     "urls": urls,
                     "repeat": form.repeat.data,
                     "shuffle": form.shuffle.data}
        data["tags"] = tags
        write_data(data)
        reader.tags = tags
        return redirect("/")
    return render_template('edit.html', form=form, tag=tag)


@ app.route('/play', methods=['GET'])
def play():
    tags = get_data()["tags"]
    tag = request.args["tag"]
    play_tag(tag)
    return redirect('/edit?tag=%s' % tag)


@ app.route('/stop', methods=['GET'])
def stop():
    print("Stopping... ")
    player.stop()
    return redirect('/edit?tag=%s' % request.args["tag"])
