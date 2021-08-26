from __future__ import unicode_literals
import random
import re
import unicodedata

import RPi.GPIO as GPIO
import vlc

from pn532 import *


class Reader():

    _TIMEOUT = 1  # seconds

    def __init__(self, player, tags) -> None:
        self.player = player
        self.tags = tags
        self.playing = False
        self.reading = True
        self.last_tag = None

    def slugify(self, value, allow_unicode=False):
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize('NFKC', value)
        else:
            value = unicodedata.normalize('NFKD', value).encode(
                'ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'[-\s]+', '-', value).strip('-_')

    def start(self) -> None:
        try:
            pn532 = PN532_SPI(debug=False, reset=20, cs=4)
            ic, ver, rev, support = pn532.get_firmware_version()
            print(
                'Found PN532 with firmware version: {0}.{1}'.format(ver, rev))
            pn532.SAM_configuration()
            print('Starting reader...')
            while self.reading:
                tag = pn532.read_passive_target(timeout=self._TIMEOUT)
                if tag is None:
                    self.player.stop()
                    self.playing = False
                    continue
                self.last_tag = tag.hex()
                if not self.playing:
                    try:
                        print("Found: %s (%s)" %
                              (self.tags[tag.hex()]["name"], tag.hex()))
                        playlist = ["downloads/" + tag.hex() + "/" + self.slugify(url) +
                                    ".mp3" for url in self.tags[tag.hex()]["urls"]]
                        if self.tags[tag.hex()]["shuffle"]:
                            random.shuffle(playlist)
                        self.player.set_media_list(vlc.MediaList(playlist))
                        if self.tags[tag.hex()]["repeat"]:
                            self.player.set_playback_mode(
                                vlc.PlaybackMode.loop)
                        else:
                            self.player.set_playback_mode(
                                vlc.PlaybackMode.default)

                        self.player.play()
                        self.playing = True
                    except Exception as x:
                        # TODO play default
                        pass

        except Exception as e:
            print(e)
