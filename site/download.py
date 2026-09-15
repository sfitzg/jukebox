#!/usr/bin/env python3
import os
import shutil
import threading
import yt_dlp
from yt_dlp.utils import DownloadError


def _download(output_dir, video_id):
    url = f'https://www.youtube.com/watch?v={video_id}'
    ydl_opts = {
        'js_runtimes': { 'node': {} },
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/audio.%(ext)s',
        # convert to mp3
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        # normalize volume in same pass
        'postprocessor_args': {
            'extractaudio+ffmpeg': ['-af', 'loudnorm'],
        },
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


class Downloader:

    def __init__(self, q, output_dir):
        self.q = q
        self.output_dir = output_dir
        self.worker = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.worker.start()

    def run(self):
        while True:
            video_id = self.q.get_next_to_download()
            shutil.rmtree(self.output_dir, ignore_errors=True)
            try:
                print(f'*** downloading {video_id}')
                _download(self.output_dir, video_id)
                print(f'*** {video_id} available')
                self.q.notify_download_complete(video_id, os.path.join(self.output_dir, 'audio.mp3'))
            except DownloadError as e:
                print(f'*** {video_id} failed')
                print(e)
                self.q_notify_download_failed(video_id)


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        _download('.', sys.argv[1])
    elif len(sys.argv) == 3:
        _download(sys.argv[2], sys.argv[1])
    else:
        sys.exit('Usage: download.py <youtube_id> [output_dir]')
