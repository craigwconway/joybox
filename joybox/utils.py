from __future__ import unicode_literals
from bs4 import BeautifulSoup
import eyed3
import json
import os.path
import re
import requests
import unicodedata
import youtube_dl


async def download(sound):
    print(f"Download {sound.source_url}")
    if not os.path.isfile(sound.local_path):
        ydl_opts = {
            "outtmpl": "%s.%s" % (sound.local_path[:-4], "%(etx)s"),
            "nocheckcertificate": True,
            "format": "bestaudio/best",
            "keepvideo": False,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            r = ydl.download([sound.source_url])


def get_data(data_file):
    with open(data_file) as f:
        data = json.load(f)
        f.close()
        return data


def get_name_from_url(url):
    junk = [" - YouTube"]
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, "html.parser")
    for title in soup.find_all("title"):
        t = title.get_text()
        for j in junk:
            t = t.replace(j, "")
        return t
    return "Unknown"


def get_name_from_metadata(filepath):
    try:
        if filepath[-4:] == ".mp3":
            metadata = eyed3.load(filepath).tag
            if metadata.title and metadata.artist:
                return f"{metadata.title} - {metadata.artist}"
            if metadata.title:
                return metadata.title
    except:
        pass
    return filepath.split("/")[-1:][0]


def slugify(value, allow_unicode=False):
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")
