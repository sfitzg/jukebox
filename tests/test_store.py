import shutil
import pytest
import os
import json
from datetime import datetime, timezone

from store import Store

TEST_DIR = '/tmp/test_jukebox/store'
SCRATCH_DIR = '/tmp/test_jukebox/scratch'
MP3 = 'audio.mp3'
INFO = 'info.json'

# Test store has max 3 entries
@pytest.fixture
def sut():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    shutil.rmtree(SCRATCH_DIR, ignore_errors=True)
    yield Store(3, TEST_DIR)
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    shutil.rmtree(SCRATCH_DIR, ignore_errors=True)

def test_id_not_found(sut):
    assert sut.find_file('deadbeef') is None

def test_creates_dir(sut):
    assert os.path.isdir(TEST_DIR)

def _make_fake_audio(location):
    os.makedirs(location, exist_ok=True)
    mp3 = os.path.join(location, MP3)
    with open(mp3, 'w') as f:
        f.write('hello')

def _make_fake_json(video_id, **kwargs):
    entry = os.path.join(TEST_DIR, video_id)
    os.makedirs(entry, exist_ok=True)
    path = os.path.join(entry, INFO)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(kwargs, f, indent=2, ensure_ascii=False)
        f.write('\n')

def test_preserves_existing_files(): # avoid fixture
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    os.makedirs(TEST_DIR)

    try:
        _make_fake_audio(os.path.join(TEST_DIR, 'deadbeef'))
        Store(3, TEST_DIR)
        expected = os.path.join(TEST_DIR, 'deadbeef', MP3)
        assert os.path.isfile(expected)
    finally:
        shutil.rmtree(TEST_DIR)

def test_id_found(sut):
    _make_fake_audio(os.path.join(TEST_DIR, 'deadbeef'))
    _make_fake_json('deadbeef', title='title0', channel='channel0',
        duration='0:10', last_access='2000-01-01T09:00:00.0+00:00')
    result = sut.find_file('deadbeef')
    assert result == os.path.join(TEST_DIR, 'deadbeef', MP3)
    assert os.path.isfile(result)

def test_save_takes_file(sut):
    _make_fake_audio(SCRATCH_DIR)
    src = os.path.join(SCRATCH_DIR, MP3)
    sut.save_file(src, 'deadbeef', 'title0', 'channel0', '0:10')
    assert not os.path.isfile(src)
    assert os.path.isfile(os.path.join(TEST_DIR, 'deadbeef', MP3))

def test_save_makes_json(sut):
    _make_fake_audio(SCRATCH_DIR)
    src = os.path.join(SCRATCH_DIR, MP3)
    sut.save_file(src, 'deadbeef', 'title0', 'channel0', '0:10')

    info = os.path.join(TEST_DIR, 'deadbeef', INFO)
    assert os.path.isfile(info)
    with open(info) as f:
        data = json.load(f)

    assert data['title'] == 'title0'
    assert data['channel'] == 'channel0'
    assert data['duration'] == '0:10'
    timestamp = data['last_access']
    print(timestamp)
    now = datetime.now(timezone.utc)
    assert 0 <= (now - datetime.fromisoformat(timestamp)).total_seconds() <= 1.0

def test_find_updates_json(sut):
    _make_fake_audio(os.path.join(TEST_DIR, 'deadbeef'))
    _make_fake_json('deadbeef', title='title0', channel='channel0',
        duration='0:10', last_access='2000-01-01T09:00:00.0+00:00')
    sut.find_file('deadbeef')
    info = os.path.join(TEST_DIR, 'deadbeef', INFO)
    with open(info) as f:
        data = json.load(f)

    assert data['title'] == 'title0'
    assert data['channel'] == 'channel0'
    assert data['duration'] == '0:10'
    timestamp = data['last_access']
    print(timestamp)
    now = datetime.now(timezone.utc)
    assert 0 <= (now - datetime.fromisoformat(timestamp)).total_seconds() <= 1.0

def test_lru(sut):
    for i in range(4):
        _make_fake_audio(SCRATCH_DIR)
        src = os.path.join(SCRATCH_DIR, MP3)
        sut.save_file(src, f'id{i}', f'title{i}', f'channel{i}', f'0:0{i}')

    assert sut.find_file('id1') is not None
    assert sut.find_file('id2') is not None
    assert sut.find_file('id3') is not None
    assert sut.find_file('id0') is None

def test_lru_honours_preserve_list(sut):
    preserve = ['id2', 'id0']
    for i in range(6):
        _make_fake_audio(SCRATCH_DIR)
        src = os.path.join(SCRATCH_DIR, MP3)
        sut.save_file(src, f'id{i}', f'title{i}', f'channel{i}', f'0:0{i}', preserve)

    assert sut.find_file('id0') is not None
    assert sut.find_file('id1') is None
    assert sut.find_file('id2') is not None
    assert sut.find_file('id3') is None
    assert sut.find_file('id4') is None
    assert sut.find_file('id5') is not None

