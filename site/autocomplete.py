#!/usr/bin/env python
import requests
import json


def _strip_yt_wrapper(text):
    PREFIX = 'window.google.ac.h('
    return text[len(PREFIX):-1] if text.startswith(PREFIX) else text


def autocomplete(part):
    ENDPOINT = 'https://suggestqueries-clients6.youtube.com/complete/search'
    params = {
        'ds': 'yt',
        'hl': 'en-gb',
        'gl': 'gb',
        'client': 'youtube',
        'q': part,
    }
    response = requests.get(ENDPOINT, params=params)
    response.raise_for_status()
    text = _strip_yt_wrapper(response.text)
    data = json.loads(text)
    suggestions = [item[0] for item in data[1]]
    return json.dumps(suggestions)


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        sys.exit('Usage: autocomplete.py <partial search term>')

    print(autocomplete(sys.argv[1]))
