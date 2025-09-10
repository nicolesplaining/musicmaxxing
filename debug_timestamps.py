#!/usr/bin/env python3
"""
Debug timestamp formats to understand duplicate detection issue
"""

import requests
from smart_db import smart_db

# Get a few scrobbles from the API
url = 'http://ws.audioscrobbler.com/2.0/'
params = {
    'method': 'user.getrecenttracks',
    'user': 'nnicolema',
    'api_key': 'b50c3e94c0f308ce124052b2e9ecfe3e',
    'format': 'json',
    'limit': 5
}

print("🔍 Checking API response...")
response = requests.get(url, params=params)
data = response.json()

if 'recenttracks' in data and 'track' in data['recenttracks']:
    tracks = data['recenttracks']['track']
    if not isinstance(tracks, list):
        tracks = [tracks]
    
    print("📡 API timestamps:")
    for i, track in enumerate(tracks[:3]):
        timestamp = track.get('date', {}).get('#text', '') if isinstance(track.get('date'), dict) else track.get('date', '')
        print(f"  {i+1}. {track.get('artist', {}).get('#text', 'Unknown')} - {track.get('name', 'Unknown')} ({timestamp})")

print("\n📊 Database timestamps:")
for i, scrobble in enumerate(smart_db.scrobbles[:3]):
    print(f"  {i+1}. {scrobble.get('artist', 'Unknown')} - {scrobble.get('name', 'Unknown')} ({scrobble.get('timestamp', 'No timestamp')})")

# Check if there are any differences
print("\n🔍 Checking for differences...")
api_timestamps = set()
for track in tracks:
    timestamp = track.get('date', {}).get('#text', '') if isinstance(track.get('date'), dict) else track.get('date', '')
    if timestamp:
        api_timestamps.add(timestamp)

db_timestamps = set()
for scrobble in smart_db.scrobbles:
    if scrobble.get('timestamp'):
        db_timestamps.add(scrobble['timestamp'])

print(f"API unique timestamps: {len(api_timestamps)}")
print(f"DB unique timestamps: {len(db_timestamps)}")

# Check if any API timestamps are not in DB
new_timestamps = api_timestamps - db_timestamps
print(f"New timestamps from API: {len(new_timestamps)}")
if new_timestamps:
    print("Sample new timestamps:")
    for ts in list(new_timestamps)[:3]:
        print(f"  - {ts}")
