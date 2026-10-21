#!/usr/bin/env python3
import requests
import json
import os
import os

MP3_DURATION_LIMIT = int(os.environ.get('MP3_DURATION_LIMIT', 1200))

def _extract(text, start, end):
    start_pos = text.index(start) + len(start)
    end_pos = text.index(end, start_pos)
    return text[start_pos:end_pos]


def _as_seconds(duration_string):
    parts = list(map(int, duration_string.split(':')))
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        m, s = parts
        return m * 60 + s
    if len(parts) == 3:
        h, m, s = parts
        return h * 3600 + m * 60 + s
    return None


def _summarize_video(video):
    try:
        duration = _as_seconds(video['lengthText']['simpleText'])

        return {
            'id': video['videoId'],
            'title': video['title']['runs'][0]['text'],
            'channel': video['ownerText']['runs'][0]['text'],
            'duration': duration,
        } if duration < MP3_DURATION_LIMIT else None
    except Exception:
        return None



def _find_videos(obj):
    if isinstance(obj, dict):
        if 'videoRenderer' in obj:
            yield obj['videoRenderer']

        for value in obj.values():
            yield from _find_videos(value)

    elif isinstance(obj, list):
        for value in obj:
            yield from _find_videos(value)


def youtube_search(query):
    ENDPOINT = 'https://www.youtube.com/results'
    params = { 'search_query': query }
    headers = { 'Accept-Language': 'en-GB,en;q=0.9', }

    response = requests.get(ENDPOINT, params=params, headers=headers)
    response.raise_for_status()

    json_text = _extract(response.text, 'ytInitialData = ', ';</script>')

    data = json.loads(json_text)

    results = []

    for video in _find_videos(data):
        candidate = _summarize_video(video)
        if candidate:
            results.append(candidate)
    return results


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        sys.exit('Usage: search.py <term>')

    for result in youtube_search(sys.argv[1]):
        print(result)
