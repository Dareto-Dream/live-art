# spotify.py

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
load_dotenv()


# === Auth Setup ===
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-read-playback-state user-modify-playback-state user-library-read user-read-currently-playing"
))

# === Playback ===

def start_music():
    """Play current or resume playback."""
    sp.start_playback()

def play():
    sp.start_playback()

def pause():
    sp.pause_playback()

def next_track():
    sp.next_track()

def previous_track():
    sp.previous_track()

def toggle_shuffle():
    state = sp.current_playback()
    if state:
        sp.shuffle(not state['shuffle_state'])

def toggle_repeat():
    state = sp.current_playback()
    if state:
        repeat_state = state['repeat_state']
        next_state = {
            'off': 'context',
            'context': 'track',
            'track': 'off'
        }[repeat_state]
        sp.repeat(next_state)

def play_playlist(uri):
    if uri == "liked":
        # Use liked songs as a seed — not perfect, but functional
        liked = sp.current_user_saved_tracks(limit=1)
        if liked['items']:
            track_uri = liked['items'][0]['track']['uri']
            sp.start_playback(uris=[track_uri])
    else:
        sp.start_playback(context_uri=uri)
        sp.shuffle(True)

# === Now Playing Info ===

def get_now_playing():
    current = sp.current_playback()
    if not current or not current.get('item'):
        return {
            "name": "Nothing Playing",
            "artist": "-",
            "cover": ""
        }

    item = current['item']
    return {
        "name": item['name'],
        "artist": ", ".join([a['name'] for a in item['artists']]),
        "cover": item['album']['images'][0]['url'] if item['album']['images'] else ""
    }
