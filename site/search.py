#!/usr/bin/env python3
import requests
import json

def _extract(text, start, end):
    start_pos = text.index(start) + len(start)
    end_pos = text.index(end, start_pos)
    return text[start_pos:end_pos]


def _summarize_video(video):
    try:
        return {
            'id': video['videoId'],
            'title': video['title']['runs'][0]['text'],
            'channel': video['ownerText']['runs'][0]['text'],
            'duration': video['lengthText']['simpleText']
        }
    except(KeyError, IndexError):
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
    return [_summarize_video(video) for video in _find_videos(data) if video]


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        sys.exit('Usage: search.py <term>')

    for result in youtube_search(sys.argv[1]):
        print(result)
