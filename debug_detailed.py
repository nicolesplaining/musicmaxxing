#!/usr/bin/env python3
"""
Detailed debug of the database update process
"""

from smart_db import smart_db
import requests
from datetime import datetime

# Get a few scrobbles from the API
url = 'http://ws.audioscrobbler.com/2.0/'
params = {
    'method': 'user.getrecenttracks',
    'user': 'nnicolema',
    'api_key': 'b50c3e94c0f308ce124052b2e9ecfe3e',
    'format': 'json',
    'limit': 10
}

print("🔍 Getting API data...")
response = requests.get(url, params=params)
data = response.json()

if 'recenttracks' in data and 'track' in data['recenttracks']:
    tracks = data['recenttracks']['track']
    if not isinstance(tracks, list):
        tracks = [tracks]
    
    print(f"📡 API returned {len(tracks)} tracks")
    
    # Process tracks like the smart_db does
    api_scrobbles = []
    for track in tracks:
        scrobble = {
            'name': track.get('name', ''),
            'artist': track.get('artist', {}).get('#text', '') if isinstance(track.get('artist'), dict) else track.get('artist', ''),
            'album': track.get('album', {}).get('#text', '') if isinstance(track.get('album'), dict) else track.get('album', ''),
            'timestamp': track.get('date', {}).get('#text', '') if isinstance(track.get('date'), dict) else track.get('date', ''),
            'loved': track.get('loved', '0') == '1',
            'playcount': int(track.get('playcount', 0)) if track.get('playcount') else 0
        }
        api_scrobbles.append(scrobble)
    
    print("📡 API scrobbles:")
    for i, scrobble in enumerate(api_scrobbles[:5]):
        print(f"  {i+1}. {scrobble['artist']} - {scrobble['name']} ({scrobble['timestamp']})")

print(f"\n📊 Database has {len(smart_db.scrobbles)} scrobbles")
print("📊 Database scrobbles (first 5):")
for i, scrobble in enumerate(smart_db.scrobbles[:5]):
    print(f"  {i+1}. {scrobble['artist']} - {scrobble['name']} ({scrobble['timestamp']})")

# Check duplicate detection
print("\n🔍 Testing duplicate detection...")
existing_timestamps = set()
for scrobble in smart_db.scrobbles:
    if scrobble.get('timestamp'):
        existing_timestamps.add(scrobble['timestamp'])

print(f"Existing timestamps in DB: {len(existing_timestamps)}")

truly_new = []
for scrobble in api_scrobbles:
    if scrobble.get('timestamp') and scrobble['timestamp'] not in existing_timestamps:
        truly_new.append(scrobble)

print(f"Truly new scrobbles: {len(truly_new)}")
if truly_new:
    print("New scrobbles:")
    for i, scrobble in enumerate(truly_new[:3]):
        print(f"  {i+1}. {scrobble['artist']} - {scrobble['name']} ({scrobble['timestamp']})")
else:
    print("No new scrobbles found - all API scrobbles are already in database")
    
    # Check if the API timestamps are actually in the database
    print("\n🔍 Checking if API timestamps are in database...")
    for scrobble in api_scrobbles[:3]:
        timestamp = scrobble.get('timestamp', '')
        if timestamp:
            if timestamp in existing_timestamps:
                print(f"  ✅ {timestamp} - FOUND in database")
            else:
                print(f"  ❌ {timestamp} - NOT FOUND in database")
