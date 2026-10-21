import os
import json
from queue import Queue
from flask import Flask, render_template, request, Response

import autocomplete as ac
import search as srch
import song_queue
import download
import player
from store import Store

MP3_CACHE = os.environ.get('MP3_CACHE')
SCRATCH = os.environ.get('JUKEBOX_TMP', '/tmp/jukebox/scratch')

if MP3_CACHE is None:
    home = os.environ.get('HOME')
    if home is None:
        raise RuntimeError('Neither MP3_CACHE nor HOME is set')
    MP3_CACHE = os.path.join(home, 'mp3_cache')

MAX_CACHE_ITEMS = 256 # TODO env var all parameters

s = Store(MAX_CACHE_ITEMS, MP3_CACHE)
q = song_queue.Queue(s)
dl = download.Downloader(q, SCRATCH)
pl = player.Player(q)

dl.start()
pl.start()

app = Flask(__name__)

@app.get('/')
def index():
    return render_template('index.html')

@app.route('/autocomplete', methods=['POST'])
def autocomplete():
    data = request.json
    query = data['query']
    return ac.autocomplete(query)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data['query']
    return srch.youtube_search(query)

@app.route('/queue', methods=['POST'])
def enqueue():
    data = request.json
    video_id = data['id']
    title = data['title']
    channel = data['channel']
    duration = data['duration']
    q.push_back(video_id, title, channel, duration)
    return {'status': 'ok'}

@app.route('/pause', methods=['POST'])
def pause():
    pl.pause()
    return {'status': 'ok'}

@app.route('/skip', methods=['POST'])
def skip():
    pl.skip()
    return {'status': 'ok'}

@app.route('/volume', methods=['POST'])
def volume():
    data = request.json
    delta = data['delta']
    pl.adjust_volume(int(delta))
    return {'status': 'ok'}

@app.get('/playback-status')
def playback_status():
    return pl.playback_status()

@app.get('/events')
def events():
    def generate():
        try:
            event_source = Queue()
            q.subscribe(event_source)
            while True:
                data = event_source.get()
                yield f'data: {json.dumps(data)}\n\n'

        finally:
            q.unsubscribe(event_source)

    return Response(generate(), mimetype='text/event-stream')
