from __future__ import unicode_literals
from pn532 import PN532_SPI
import vlc
import random
import re
import unicodedata

import RPi.GPIO as GPIO

GPIO.setwarnings(False)


class Reader:

    TIMEOUT = 1  # seconds
    DEFAULT = "downloads/default/endline.wav"

    def __init__(self, player, playlist_map) -> None:
        self.player = player
        self.playlist_map = playlist_map
        self.playing = False
        self.reading = True
        self.last_tag = None

    def start(self) -> None:
        try:
            pn532 = PN532_SPI(debug=False, reset=20, cs=4)
            ic, ver, rev, support = pn532.get_firmware_version()
            print("Found PN532: {0}.{1}".format(ver, rev))
            pn532.SAM_configuration()
            print("Starting reader...")
            while self.reading:
                tag = pn532.read_passive_target(timeout=self.TIMEOUT)
                if tag is None:
                    self.player.stop()
                    self.playing = False
                    continue
                self.last_tag = str(tag.hex())
                if not self.playing:
                    print(f"looking for match: {self.last_tag}")
                    try:
                        joycon = self.playlist_map[self.last_tag]
                        print(f"Found: {joycon['name']}")
                        playlist = joycon["playlist"]
                        if joycon["shuffle"]:
                            random.shuffle(playlist)
                        self.player.set_media_list(vlc.MediaList(playlist))
                        if joycon["repeat"]:
                            self.player.set_playback_mode(vlc.PlaybackMode.loop)
                        else:
                            self.player.set_playback_mode(vlc.PlaybackMode.default)
                        self.player.play()
                        self.playing = True
                    except Exception as x:
                        print(x)
                        self.player.set_media_list(vlc.MediaList([self.DEFAULT]))
                        self.player.play()
                        self.playing = False

        except Exception as e:
            print(e)
