import os
import shutil
import json
from datetime import datetime, timezone

MP3 = 'audio.mp3'
INFO = 'info.json'

def _save_info(path, title, channel, duration):
    data = {
        'title': title,
        'channel': channel,
        'duration': duration,
        'last_access': datetime.now(timezone.utc).isoformat(),
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')


class Store:

    def __init__(self, max_size, location):
        if max_size < 1:
            raise ValueError('max_size must be at least 1')
        self.max_size = max_size
        self.location = location

        if os.path.exists(location):
            if not os.path.isdir(location):
                raise NotADirectoryError(location)
        else:
            os.makedirs(location)

    def _info_file(self, video_id):
        return os.path.join(self.location, video_id, INFO)

    def _audio_file(self, video_id):
        return os.path.join(self.location, video_id, MP3)

    def _get_last_access(self, video_id):
        with open(self._info_file(video_id)) as f:
            data = json.load(f)
        return data['last_access']

    def _make_room(self, preserve_list):
        entries = os.listdir(self.location)
        if len(entries) < self.max_size:
            return

        excess_items = 1 + len(entries) - self.max_size

        if preserve_list:
            entries = list(set(entries) - set(preserve_list))

        candidates = sorted(entries, key=self._get_last_access)

        i = 0
        while i < len(candidates) and excess_items:
            shutil.rmtree(os.path.join(self.location, candidates[i]))
            excess_items -= 1
            i += 1
        
# TODO errors
    def find_file(self, video_id):
        mp3 = self._audio_file(video_id)
        if not os.path.isfile(mp3):
            return None
        info = self._info_file(video_id)
        if not os.path.isfile(info):
            return None
        with open(info) as f:
            data = json.load(f)
        _save_info(info, data['title'], data['channel'], data['duration'])
        return mp3

    def save_file(self, src, video_id, title, channel, duration, preserve_list=None):
        self._make_room(preserve_list)
        dest = os.path.join(self.location, video_id)
        os.makedirs(dest)
        shutil.move(src, dest)
        path = self._info_file(video_id)
        _save_info(path, title, channel, duration)
        return self._audio_file(video_id) # TODO test return value
