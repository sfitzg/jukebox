#!/usr/bin/env python3
import time
import threading
import os

import vlc

class Player:

    def __init__(self, q):
        self.q = q
        self.worker = threading.Thread(target=self.run, daemon=True)
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.event_manager = self.player.event_manager()
        self.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end)
        self.event_manager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_error)
        self.first_one = True
        self.error = False
        self.done = threading.Event()

    def start(self):
        self.worker.start()

    def pause(self):
        if self.player:
            self.player.pause()

    def skip(self):
        if self.player:
            self.player.stop()
            self.error = False
            self.done.set()

    def _on_end(self, event):
        self.error = False
        self.done.set()

    def _on_error(self, event):
        self.error = True
        self.done.set()

    def _play(self, path):
        self.error = False
        print(f'Playing {path}')
        self.player.set_media(self.instance.media_new(path))
        self.player.play()

        # Work around segfault if we set volume too soon
        if self.first_one:
            time.sleep(0.1)
            self.first_one = False

        self.player.audio_set_volume(50)
        self.done.wait()
        self.done.clear()
        if self.error:
            print('error')
        else:
            print('success')

    def run(self):
        while True:
            mp3 = self.q.get_next_to_play()
            print(f'### playing {mp3}')
            self._play(mp3)
            print(f'### {mp3} play done')


