import pytest
import time
from concurrent.futures import ThreadPoolExecutor
import queue

from song_queue import Queue

class FakeStoreNotFound:
    def find_file(self, video_id):
        return None

    def save_file(self, tmp_path, video_id, title, channel, duration, preserve_list):
        return f'bar/{video_id}'


@pytest.fixture
def sut():
    store = FakeStoreNotFound()
    return Queue(store, debug=True)

def test_basic_fifo(sut):
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    sut.push_back('23', 'title1', 'channel1', 'duration1')
    assert sut.get_next_to_download() == '42'
    assert len(sut.items) == 2

def test_push_front(sut):
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    sut.push_front('23', 'title1', 'channel1', 'duration1')
    assert sut.get_next_to_download() == '23'
    assert len(sut.items) == 2

def test_download_state(sut):
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    sut.push_back('23', 'title1', 'channel1', 'duration1')
    sut.notify_download_complete('42', 'foo')
    assert sut.get_next_to_download() == '23'
    assert sut.get_next_to_play() == 'bar/42'
    assert len(sut.items) == 1

def test_stale_download_completion(sut):
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    sut.push_back('23', 'title1', 'channel1', 'duration1')
    sut.notify_download_complete(100, 'foo')
    assert len(sut.items) == 2

def test_stale_cancel(sut):
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    sut.push_back('23', 'title1', 'channel1', 'duration1')
    sut.cancel(100)
    assert len(sut.items) == 2

def test_cancel(sut):
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    sut.push_back('23', 'title1', 'channel1', 'duration1')
    sut.cancel('42')
    assert len(sut.items) == 1
    assert sut.get_next_to_download() == '23'

def test_dupe_ignored(sut):
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    sut.push_back('23', 'title1', 'channel1', 'duration1')
    sut.push_back('23', 'title1', 'channel1', 'duration1')
    assert len(sut.items) == 2
    assert sut.get_next_to_download() == '42'

def test_dupe_at_front_moves_item(sut):
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    sut.push_back('23', 'title1', 'channel1', 'duration1')
    sut.push_front('23', 'title1', 'channel1', 'duration1')
    assert len(sut.items) == 2
    assert sut.get_next_to_download() == '23'

def test_dupe_at_front_preserves_availability(sut):
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    sut.notify_download_complete('42', 'foo')
    sut.push_front('23', 'title1', 'channel1', 'duration1')
    sut.push_front('42', 'title0', 'channel0', 'duration0')
    sut.push_front('7', 'title2', 'channel2', 'duration2')
    assert sut.get_next_to_play() == 'bar/42'
    assert len(sut.items) == 2

def test_dupe_at_back_preserves_availability(sut):
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    sut.notify_download_complete('42', 'foo')
    sut.push_back('23', 'title1', 'channel1', 'duration1')
    sut.notify_download_complete('23', 'foo')
    sut.push_back('7', 'title2', 'channel2', 'duration2')
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    assert sut.get_next_to_play() == 'bar/42'
    assert len(sut.items) == 2

def test_play_skips_unavailable_items(sut):
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    sut.push_back('23', 'title1', 'channel1', 'duration1')
    sut.push_front('7', 'title2', 'channel2', 'duration2')
    sut.notify_download_complete('23', 'foo')
    assert sut.get_next_to_play() == 'bar/23'

def test_download_waits_for_item(sut):
    with ThreadPoolExecutor() as executor:
        future = executor.submit(sut.get_next_to_download)
        time.sleep(0.01)
        assert not future.done()
        sut.push_back('42', 'title0', 'channel0', 'duration0')
        assert future.result(timeout=1) == '42'

def test_play_waits_for_item(sut):
    with ThreadPoolExecutor() as executor:
        future = executor.submit(sut.get_next_to_play)
        sut.push_back('42', 'title0', 'channel0', 'duration0')
        time.sleep(0.01)
        assert not future.done()
        sut.notify_download_complete('42', 'foo')
        assert future.result(timeout=1) == 'bar/42'

def test_initial_q_event(sut):
    sut.push_back('42', 't0', 'c0', 'd0')
    sut.push_back('23', 't1', 'c1', 'd1')
    sut.notify_download_complete('42', 'foo')
    expected_state = { 'now_playing': None, 'queued': [
      { 'video_id': '42', 'title': 't0', 'channel': 'c0', 'duration': 'd0', 'available': True, 'failed': False },
      { 'video_id': '23', 'title': 't1', 'channel': 'c1', 'duration': 'd1', 'available': False, 'failed': False}]}
    q1 = queue.Queue()
    q2 = queue.Queue()
    sut.subscribe(q1)
    sut.subscribe(q2)
    assert q1.qsize() == 1
    assert q1.get() == expected_state
    assert q2.qsize() == 1
    assert q2.get() == expected_state

def test_broadcast(sut):
    q1 = queue.Queue()
    q2 = queue.Queue()
    sut.subscribe(q1)
    sut.subscribe(q2)
    sut.push_back('42', 't0', 'c0', 'd0')
    sut.notify_download_complete('42', 'foo')
    sut.push_back('23', 't1', 'c1', 'd1')
    expected_state_0 = {'now_playing': None, 'queued': [] }
    expected_state_1 = { 'now_playing': None, 'queued': [
      { 'video_id': '42', 'title': 't0', 'channel': 'c0', 'duration': 'd0', 'available': False, 'failed': False }]}
    expected_state_2 = { 'now_playing': None, 'queued': [
      { 'video_id': '42', 'title': 't0', 'channel': 'c0', 'duration': 'd0', 'available': True, 'failed': False }]}
    expected_state_3 = { 'now_playing': None, 'queued': [
      { 'video_id': '42', 'title': 't0', 'channel': 'c0', 'duration': 'd0', 'available': True, 'failed': False },
      { 'video_id': '23', 'title': 't1', 'channel': 'c1', 'duration': 'd1', 'available': False, 'failed': False }]}

    assert q1.qsize() == 4
    assert q1.get() == expected_state_0
    assert q1.get() == expected_state_1
    assert q1.get() == expected_state_2
    assert q1.get() == expected_state_3

    assert q2.qsize() == 4
    assert q2.get() == expected_state_0
    assert q2.get() == expected_state_1
    assert q2.get() == expected_state_2
    assert q2.get() == expected_state_3


class FakeStoreFound:
    def find_file(self, video_id):
        return f'bar/{video_id}'

    def save_file(self, tmp_path, video_id, title, channel, duration, preserve_list):
        pass

def test_found_in_cache():
    store = FakeStoreFound()
    sut = Queue(store, debug=True)
    sut.push_back('42', 'title0', 'channel0', 'duration0')
    assert len(sut.items) == 1
    # don't need to wait for notify_download_complete()
    assert sut.get_next_to_play() == 'bar/42'
    assert len(sut.items) == 0
