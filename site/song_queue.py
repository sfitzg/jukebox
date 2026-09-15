from threading import Lock, Condition
from dataclasses import dataclass, asdict

@dataclass
class Entry:
    video_id: str
    title: str
    channel: str
    duration: str
    path: str   # audio file or None if not yet downloaded
    failed: bool

def _unpack_one(entry):
    return {
        'video_id': entry.video_id,
        'title': entry.title,
        'channel': entry.channel,
        'duration': entry.duration,
        'available': entry.path is not None,
        'failed': entry.failed
    }

class Queue:
    def __init__(self, store, *, debug=False):
        self.lock = Lock()
        self.changed = Condition(self.lock)
        self.items = []
        self.observers = set()
        self.store = store
        self.debug = debug
        self.now_playing = None
        self.consecutive_failures = 0

    def push_front(self, video_id, title, channel, duration):
        with self.changed:
            # if it's already queued, move it to front
            item = self._pop_first_item_matching(lambda item: item.video_id == video_id)
            if not item:
                # otherwise, check if it's in the file store and enqueue
                path = self.store.find_file(video_id)
                item = Entry(video_id, title, channel, duration, path, False)
            self.items.insert(0, item)
            self._check_invariant()
            self._broadcast()
            self.changed.notify_all()

    def push_back(self, video_id, title, channel, duration):
        with self.changed:
            # if it's already queued, do nothing
            item = self._find_first_item_matching(lambda item: item.video_id == video_id)
            if not item:
                # otherwise, check if it's in the file store and enqueue
                path = self.store.find_file(video_id)
                self.items.append(Entry(video_id, title, channel, duration, path, False))
                self._check_invariant()
                self._broadcast()
                self.changed.notify_all()

    def cancel(self, video_id):
        with self.changed:
            item = self._pop_first_item_matching(lambda item: item.video_id == video_id)
            self._check_invariant()
            if item:
                self._broadcast()
                self.changed.notify_all()

    def _preserve_list(self):
        queued_ids = [item.video_id for item in self.items]
        if self.now_playing:
            queued_ids.append(self.now_playing.video_id)
        return queued_ids

    def notify_download_complete(self, video_id, tmp_path):
        with self.changed:
            self.consecutive_failures = 0
            item = self._find_first_item_matching(lambda item: item.video_id == video_id)
            if item:
                path = self.store.save_file(tmp_path, video_id, item.title, item.channel, item.duration,
                    self._preserve_list())
                item.path = path
                item.failed = False
                self._check_invariant()
                self._broadcast()
                self.changed.notify_all()

    def notify_download_failed(self, video_id):
        with self.changed:
            self.consecutive_failures += 1
            item = self._pop_first_item_matching(lambda item: item.video_id == video_id)
            if item:
                # mark and move to end
                item.failed = True
                self.items.append(item)

    # keeps item on queue.
    def get_next_to_download(self):
        while True:
            with self.changed:
                item = self._find_first_item_matching(lambda item: item.path is None and not item.failed)
                if item:
                    return item.video_id
                # try a failed one if nothing happens for a while
                backoff = min(10, self.consecutive_failures) # cap at 1024s
                if not self.changed.wait(2 ** backoff):
                    item = self._find_first_item_matching(lambda item: item.path is None)
                    if item:
                        return item.video_id


    # removes item from queue
    def get_next_to_play(self):
        while True:
            with self.changed:
                item = self._pop_first_item_matching(lambda item: item.path is not None)
                self._check_invariant()
                if item:
                    self.now_playing = item
                    self._broadcast()
                    return item.path
                self.changed.wait()

    def subscribe(self, observer):
        with self.changed:
            self.observers.add(observer)
            observer.put(self._unpack_entries())

    def unsubscribe(self, observer):
        with self.changed:
            self.observers.remove(observer)

    # unsynchronized, internal use only
    def _broadcast(self):
        for observer in self.observers:
            # TODO - real data and decide who owns conversion to json
            observer.put(self._unpack_entries())

    # unsynchronized, internal use only
    def _unpack_entries(self):
        return {
            'now_playing': None if self.now_playing is None else _unpack_one(self.now_playing),
            'queued': [ _unpack_one(item) for item in self.items ]
        }

    # unsynchronized, internal use only
    def _find_first_item_matching(self, predicate):
        i = self._find_first_index_matching(predicate)
        return self.items[i] if i is not None else None

    # unsynchronized, internal use only
    def _pop_first_item_matching(self, predicate):
        i = self._find_first_index_matching(predicate)
        return self.items.pop(i) if i is not None else None

    # unsynchronized, internal use only
    def _find_first_index_matching(self, predicate):
        for i in range(len(self.items)):
            if predicate(self.items[i]):
                return i
        return None

    # unsynchronized, internal use only
    def _check_invariant(self):
        if self.debug:
            # no dupes
            ids = [item.video_id for item in self.items]
            assert len(ids) == len(set(ids))
