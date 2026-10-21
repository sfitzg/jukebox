const events = new EventSource('/events');

// TODO change name if it is to handle other things
class SearchService {
    autocomplete(input) {
        // Forward to flask endpoint
        return fetch('/autocomplete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({query: input}),
        }).then(response => response.json());
    }

    search(input) {
        // Forward to flask endpoint
        return fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({query: input}),
        }).then(response => response.json());
    }

    enqueue(id, title, channel, duration) {
        // Forward to flask endpoint
        return fetch('/queue', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({id, title, channel, duration}),
        }).then(response => response.json());
    }

    pause() {
        // Forward to flask endpoint
        return fetch('/pause', {
            method: 'POST',
        }).then(response => response.json());
    }

    skip() {
        // Forward to flask endpoint
        return fetch('/skip', {
            method: 'POST',
        }).then(response => response.json());
    }

    volume(delta) {
        return fetch('/volume', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({delta}),
        }).then(response => response.json());
    }

    playback_status() {
        return fetch('/playback-status')
            .then(response => response.json());
    }

    listen(handler) {
        events.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handler(data);
        };
    }
}

export default SearchService;
