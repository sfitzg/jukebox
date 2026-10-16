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
        self.error = False
        self.done = threading.Event()
        self.volume_lock = threading.Lock() # protect self.first_one, self.volume
        self.first_one = True
        self.volume = 50

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
        with self.volume_lock:
            if self.first_one:
                time.sleep(0.1)
                self.first_one = False
            self.player.audio_set_volume(self.volume)

        self.done.wait()
        self.done.clear()
        if self.error:
            print('error')
        else:
            print('success')

    def adjust_volume(self, delta):
        with self.volume_lock:
            self.volume = max(0, min(100, self.volume + delta))
            if self.first_one:
                return # not safe yet
            self.player.audio_set_volume(self.volume)

    def run(self):
        while True:
            mp3 = self.q.get_next_to_play()
            print(f'### playing {mp3}')
            self._play(mp3)
            print(f'### {mp3} play done')
