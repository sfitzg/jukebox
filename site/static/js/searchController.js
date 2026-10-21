function populateListElement(document, element, strings) {
    element.replaceChildren();
    for (const s of strings) {
        const item = document.createElement('li');
        item.textContent = s;
        element.appendChild(item);
    }
}

function to_duration_string(s) {
    const h = Math.floor(s / 3600);
    const m = Math.floor(s % 3600 / 60);
    const secs = s % 60;

    if (h) return `${h}:${String(m).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    return `${m}:${String(secs).padStart(2, '0')}`;
}

function makeResultLI(document, r) {
    const item = document.createElement('li');
    item.className = 'search-result';
    item.dataset.id = r.id;
    item.dataset.title = r.title;
    item.dataset.channel = r.channel;
    item.dataset.duration = r.duration;

    // video id determines the url for the thumbnail
    const thumb = document.createElement('img');
    thumb.className = 'results-thumbnail';
    thumb.src = `https://i.ytimg.com/vi/${r.id}/hqdefault.jpg`;
    thumb.alt = '';

    const title = document.createElement('div');
    title.className = 'results-title is-size-5';
    title.textContent = r.title;

    const channel = document.createElement('div');
    channel.className = 'results-channel is-size-7';
    channel.textContent = r.channel;

    const duration = document.createElement('div');
    duration.className = 'results-duration is-size-4';
    duration.textContent = to_duration_string(r.duration);

    const playImg = document.createElement('img');
    playImg.src = '/static/icons/play-fill.svg';

    const play = document.createElement('button');
    play.type = 'button';
    play.className = 'results-play-button button is-primary';
    play.append(playImg);

    const text = document.createElement('div');
    text.className = 'results-text';
    text.append(title, channel);

    const info = document.createElement('div');
    info.className = 'results-info';
    info.append(text, duration, play);

    item.append(thumb, info);
    return item;
}

function makeQueueLI(document, r) {
    const item = document.createElement('li');
    item.className = 'queue-item';
    item.dataset.id = r.video_id;
    item.dataset.title = r.title;
    item.dataset.channel = r.channel;
    item.dataset.duration = r.duration;

    // video id determines the url for the thumbnail
    const thumb = document.createElement('img');
    thumb.className = 'queue-thumbnail';
    thumb.src = `https://i.ytimg.com/vi/${r.video_id}/hqdefault.jpg`;
    thumb.alt = '';

    const title = document.createElement('div');
    title.className = 'queue-title is-size-5';
    title.textContent = r.title;

    const channel = document.createElement('div');
    channel.className = 'queue-channel is-size-7';
    channel.textContent = r.channel;

    const duration = document.createElement('div');
    duration.className = 'queue-duration is-size-4';
    duration.textContent = to_duration_string(r.duration);

    const text = document.createElement('div');
    text.className = 'queue-text';
    text.append(title, channel);

    const x = document.createElement('img');
    x.src = '/static/icons/x.svg';

    const cancel = document.createElement('button');
    cancel.type = 'button';
    cancel.className = 'cancel-button button is-danger';
    cancel.append(x);

    item.append(thumb, text, duration, cancel);
    return item;
}

class SearchController {

    constructor(document, service) {

        this.document = document;
        this.service = service;
        this.autocompleteRequestId = 0;
        this.searchRequestId = 0;

        this.searchBox = document.getElementById('yt-search');
        this.searchForm = document.getElementById('search-form');
        this.suggestionList = document.getElementById('suggestions');
        this.resultList = document.getElementById('results');
        this.queueList = document.getElementById('queue');

        this.nowPlayingContainer = document.getElementById('now-playing');
        this.nowPlayingThumbnail = document.getElementById('now-playing-thumbnail');
        this.nowPlayingTitle = document.getElementById('now-playing-title');
        this.nowPlayingChannel = document.getElementById('now-playing-channel');
        this.nowPlayingDuration = document.getElementById('now-playing-duration');

        this.pauseResumeButton = document.getElementById('pause');
        this.pauseResumeImage = document.querySelector('#pause img');
        this.skipButton = document.getElementById('skip');
        this.volumeDownButton = document.getElementById('volume-down');
        this.volumeUpButton = document.getElementById('volume-up');

        service.listen((data) => {
            this.queueList.replaceChildren();
            for (const entry of data.queued) {
                const item = makeQueueLI(document, entry)
                this.queueList.appendChild(item);
            }
            if (data.now_playing) {
                this.nowPlayingThumbnail.src = `https://i.ytimg.com/vi/${data.now_playing.video_id}/hqdefault.jpg`;
                this.nowPlayingTitle.textContent = data.now_playing.title;
                this.nowPlayingChannel.textContent = data.now_playing.channel;
                this.nowPlayingDuration.textContent = to_duration_string(data.now_playing.duration);
                this.pauseResumeImage.src = '/static/icons/pause-fill.svg';

                if (this.nowPlayingContainer.hidden) {
                    // Poll pause/playing status and time remaining
                    this.nowPlayingContainer.dataset.timer = setInterval(async () => {
                        const data = await service.playback_status();
                        const remaining = Math.round(data.remaining / 1000);
                        if (data.state == 'paused') {
                            this.pauseResumeImage.src = '/static/icons/play-fill.svg';
                        }
                        else {
                            this.pauseResumeImage.src = '/static/icons/pause-fill.svg';
                        }

                        this.nowPlayingDuration.textContent = to_duration_string(remaining);
                    }, 200);

                    this.nowPlayingContainer.hidden = false;
                }
            }
            else if (!this.nowPlayingContainer.hidden) {
                clearInterval(this.nowPlayingContainer.dataset.timer);
                this.nowPlayingContainer.dataset.timer = null;
                this.nowPlayingContainer.hidden = true;
            }
        });

        this.searchBox.addEventListener('input', async (event) => {
            const id = ++this.autocompleteRequestId;
            const input = event.target.value;
            if (input.trim() == '') {
                this.suggestionList.replaceChildren();
                return;
            }
            const results = await service.autocomplete(input);

            if (id == this.autocompleteRequestId) {
                populateListElement(document, this.suggestionList, results);
            }
        });

        this.searchForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            await this.doSearch();
        });

        this.suggestionList.addEventListener('click', async (event)  => {
            const item = event.target.closest('li');
            if (!item) return;
            this.searchBox.value = item.textContent;
            await this.doSearch();
        });

        this.resultList.addEventListener('click', async (event)  => {
            if (!event.target.closest('.results-play-button')) return;
            const item = event.target.closest('li');
            if (!item) return;

            this.suggestionList.replaceChildren();
            this.resultList.replaceChildren();
            this.searchBox.value = '';

            await service.enqueue(item.dataset.id, item.dataset.title,
                    item.dataset.channel, item.dataset.duration);
        });

        this.queueList.addEventListener('click', async (event)  => {
            if (!event.target.closest('.cancel-button')) return;
            const item = event.target.closest('li');
            if (!item) return;

            await service.cancel(item.dataset.id);
        });

        this.pauseResumeButton.addEventListener('click', (event)  => {
            service.pause();
        });

        this.skipButton.addEventListener('click', (event)  => {
            service.skip();
        });

        this.volumeDownButton.addEventListener('click', (event)  => {
            service.volume(-5);
        });

        this.volumeUpButton.addEventListener('click', (event)  => {
            service.volume(5);
        });
    }

    async doSearch() {
        this.suggestionList.replaceChildren();
        const input = this.searchBox.value;

        if (input.trim() == '') {
            return;
        }
        const id = ++this.searchRequestId;
        const results = await this.service.search(input);

        if (id != this.searchRequestId) {
            return;
        }
        this.resultList.replaceChildren();

        for (const r of results) {
            const item = makeResultLI(this.document, r);
            this.resultList.appendChild(item);
        }
    }

}

export default SearchController;
