import asyncio
import atexit
import os
import threading


import vlc

from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy

from reader import Reader
from utils import download, get_data, slugify, get_name_from_url, get_name_from_metadata


POLL_INTERVAL = 0.5  # half a second
data_file = "data.json"  # TODO remove
data_map = {"current_tag": None, "tags": get_data("data.json")["tags"]}  # TODO remove
player = vlc.MediaListPlayer()
reader = Reader(player, {})
t_lock = threading.Lock()
t_reader = threading.Thread()


db = SQLAlchemy()


def map_playlists(joycons):
    playlist_map = {}
    for joycon in joycons:
        playlist_map[joycon.id] = {}
        playlist_map[joycon.id]["name"] = joycon.name
        playlist_map[joycon.id]["playlist"] = [s.local_path for s in joycon.sounds]
        playlist_map[joycon.id]["repeat"] = joycon.repeat
        playlist_map[joycon.id]["shuffle"] = joycon.shuffle
    return playlist_map


def create_app():

    app = Flask(__name__)

    app.config["SECRET_KEY"] = "x3HqRBL-9GBo._VmJHY-"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///joybox.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.app_context().push()

    db.init_app(app)
    db.create_all()

    reader.playlist_map = map_playlists(Joycon.query.all())

    def interrupt():
        global t_reader
        t_reader.cancel()

    def initReader():
        global reader
        global t_reader
        with t_lock:
            try:
                reader.start()
            except:
                pass
        t_reader = threading.Timer(POLL_INTERVAL, initReader, ())
        t_reader.start()

    def start():
        global t_reader
        t_reader = threading.Timer(POLL_INTERVAL, initReader, ())
        t_reader.start()

    start()
    atexit.register(interrupt)

    return app


from models import Joycon, Sound

app = create_app()


@app.route("/bootstrap", methods=["GET"])
def bootstrap():
    if Joycon.query.count() == 0:
        tags = data_map["tags"]
        for id in tags.keys():
            joycon = Joycon()
            joycon.id = id
            joycon.name = tags[id]["name"]
            joycon.repeat = tags[id]["repeat"]
            joycon.shuffle = tags[id]["shuffle"]
            db.session.add(joycon)
            db.session.commit()
            print(f"Saved {joycon.name}")
            order = 0
            for url in tags[id]["urls"]:
                sound = Sound()
                sound.joycon_id = joycon.id
                sound.source_url = url
                sound.local_path = f"downloads/{joycon.id}/{slugify(url)}.mp3"
                sound.order = order
                order = order + 1
                sound.name = get_name_from_url(sound.source_url)
                db.session.add(sound)
                db.session.commit()
                print(f"Saved {sound.name}")
        return f"Loaded {Joycon.query.count()} joycons!"
    return "nope"


@app.route("/", methods=["GET"])
def index():
    joycons = Joycon.query.order_by(Joycon.name).all()
    return render_template("index.html", joycons=joycons)


@app.route("/deleteJoycon", methods=["POST"])
def delete_joycon():
    joycon = Joycon.query.get(request.form.get("jid"))
    reader.joycon_map.pop(joycon.id)
    sounds = joycon.sounds
    for sound in sounds:
        try:
            os.remove(sound.local_path)
        except:
            pass
    db.session.delete(joycon)
    db.session.commit()
    reader.playlist_map = map_playlists(Joycon.query.all())
    return redirect("/")


@app.route("/deleteSound", methods=["GET"])
def delete_sound():
    sound = Sound.query.get(request.args["sid"])
    joycon_id = sound.joycon_id
    try:
        os.remove(sound.local_path)
    except:
        pass
    db.session.delete(sound)
    db.session.commit()
    sounds = Sound.query.filter_by(joycon_id=joycon_id)
    order = 0
    for sound in sounds:
        sound.order = order
        order = order + 1
        db.session.merge(sound)
        db.session.commit()
    reader.playlist_map = map_playlists(Joycon.query.all())
    return redirect(f"/edit?jid={joycon_id}")


@app.route("/orderUp", methods=["GET"])
def order_up():
    sound = Sound.query.get(request.args["sid"])
    joycon = Joycon.query.get(sound.joycon_id)
    sounds = joycon.sounds
    if sound.order + 1 < len(sounds):
        sounds[sound.order + 1].order = sound.order
        db.session.merge(sounds[sound.order + 1])
        db.session.commit()
        sound.order = sound.order + 1
        db.session.merge(sound)
        db.session.commit()
    reader.playlist_map = map_playlists(Joycon.query.all())
    return redirect(f"/edit?jid={sound.joycon_id}")


@app.route("/orderDown", methods=["GET"])
def order_down():
    sound = Sound.query.get(request.args["sid"])
    joycon = Joycon.query.get(sound.joycon_id)
    sounds = joycon.sounds
    if sound.order - 1 >= 0:
        sounds[sound.order - 1].order = sound.order
        db.session.merge(sounds[sound.order - 1])
        db.session.commit()
        sound.order = sound.order - 1
        db.session.merge(sound)
        db.session.commit()
    reader.playlist_map = map_playlists(Joycon.query.all())
    return redirect(f"/edit?jid={sound.joycon_id}")


@app.route("/download", methods=["POST"])
async def download_sounds():
    if request.method == "POST":
        sound = Sound()
        sound.joycon_id = request.form.get("jid")
        sound.source_url = request.form.get("url")
        sound.order = Sound.query.filter_by(joycon_id=sound.joycon_id).count()
        sound.local_path = (
            f"downloads/{sound.joycon_id}/{slugify(sound.source_url)}.mp3"
        )
        sound.name = get_name_from_url(sound.source_url)
        db.session.merge(sound)
        db.session.commit()
        print("New Sound", sound)
        try:
            print("call download")
            asyncio.create_task(download(sound))
        except:
            print("download error")
        reader.playlist_map = map_playlists(Joycon.query.all())
    return redirect(f"/edit?jid={sound.joycon_id}")


@app.route("/upload", methods=["POST"])
def upload_sounds():
    if request.method == "POST":
        jid = request.form.get("jid")
        files = request.files.getlist("files")
        joycon = Joycon.query.get(jid)
        order = len(joycon.sounds)
        for file in files:
            filename = os.path.join("downloads", jid, file.filename)
            print(filename)
            file.save(filename)
            sound = Sound()
            sound.joycon_id = jid
            sound.local_path = filename
            sound.order = order
            order = order + 1
            sound.name = get_name_from_metadata(filename)
            db.session.merge(sound)
            db.session.commit()
        reader.playlist_map = map_playlists(Joycon.query.all())
    return redirect(f"/edit?jid={jid}")


@app.route("/edit", methods=["GET", "POST"])
async def edit():
    joycon = Joycon()
    args = request.args
    jid = args["jid"] if "jid" in args else ""
    if request.method == "GET":
        print(f"Edit {jid}")
        joycon = Joycon.query.get(jid)
    if request.method == "POST":
        jid = request.form.get("id")
        print(f"Save {jid}")
        if not jid:
            try:  # get tag from reader
                jid = reader.last_tag
                print(f"New joycon {jid}")
            except:  # no tag on reader
                pass
        joycon.id = jid
        joycon.name = request.form.get("name")
        joycon.repeat = (
            bool(request.form.get("repeat")) if request.form.get("repeat") else False
        )
        joycon.shuffle = (
            bool(request.form.get("shuffle")) if request.form.get("shuffle") else False
        )
        db.session.merge(joycon)
        db.session.commit()
        reader.playlist_map = map_playlists(Joycon.query.all())
        return redirect("/")
    return render_template("edit.html", joycon=joycon)


@app.route("/play", methods=["GET"])
def play():
    joycon = Joycon.query.get(request.args["jid"])
    playlist = [sound.local_path for sound in joycon.sounds]
    print("PLAYLIST: ", playlist)
    player.set_media_list(vlc.MediaList(playlist))
    player.play()
    return redirect(f"/edit?jid={joycon.id}")


@app.route("/playSound", methods=["GET"])
def play_sound():
    sound = Sound.query.get(request.args["sid"])
    joycon = Joycon.query.get(sound.joycon_id)
    playlist = [sound.local_path for sound in joycon.sounds]
    print("PLAYLIST: ", playlist)
    player.set_media_list(vlc.MediaList(playlist))
    for _ in range(0, sound.order + 1):
        player.next()
    player.play()
    return redirect(f"/edit?jid={joycon.id}")


@app.route("/stop", methods=["GET"])
def stop():
    player.stop()
    return redirect(f"/edit?jid={request.args['jid']}")


@app.route("/previous", methods=["GET"])
def previous():
    player.previous()
    return redirect(f"/edit?jid={request.args['jid']}")


@app.route("/next", methods=["GET"])
def next():
    player.next()
    return redirect(f"/edit?jid={request.args['jid']}")
