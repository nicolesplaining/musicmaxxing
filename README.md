# Last.fm API Client Usage Guide

## Quick Start

### 1. Get a Last.fm API Key
1. Go to [https://www.last.fm/api/account/create](https://www.last.fm/api/account/create)
2. Sign in with your Last.fm account
3. Create a new API account
4. Copy your API key

### 2. Basic Usage

```python
from lastfm_client import LastFMClient

# Initialize the client
client = LastFMClient(api_key="your_api_key_here")

# Get your top tracks
top_tracks = client.get_user_top_tracks("your_username", limit=10)

for track in top_tracks:
    print(f"{track.artist} - {track.name} ({track.playcount} plays)")
```

## Main Features

### Time-Based Queries
```python
from lastfm_client import TimeRange, LastFMClient
from datetime import datetime, timedelta

client = LastFMClient(api_key="your_api_key")

# Last week
last_week = TimeRange.from_days_ago(7)
recent_tracks = client.get_user_recent_tracks("username", time_range=last_week)

# Custom time range
start = datetime(2024, 1, 1)
end = datetime(2024, 1, 31)
january = TimeRange(start, end)
january_tracks = client.get_user_recent_tracks("username", time_range=january)
```

### Get Different Types of Data
```python
# Top tracks
top_tracks = client.get_user_top_tracks("username", limit=20)

# Top artists
top_artists = client.get_user_top_artists("username", limit=20)

# Top albums
top_albums = client.get_user_top_albums("username", limit=20)

# Recent tracks
recent_tracks = client.get_user_recent_tracks("username", limit=50)
```

### Comprehensive Statistics
```python
# Get all stats for a time period
stats = client.get_user_stats("username", time_range=last_month)

print(f"Total plays: {stats['total_plays']}")
print(f"Unique tracks: {stats['unique_tracks']}")
print(f"Diversity score: {stats['diversity_score']:.2%}")
```

### Search Your Activity
```python
# Search for specific tracks/artists
results = client.search_user_activity("username", "beatles", time_range=last_month)
for track in results:
    print(f"{track.artist} - {track.name}")
```

## Predefined Time Ranges
```python
from lastfm_client import create_time_ranges

time_ranges = create_time_ranges()

# Available ranges:
# - last_week
# - last_month  
# - last_3_months
# - last_6_months
# - last_year
# - this_year
# - last_year_full

stats = client.get_user_stats("username", time_ranges['last_month'])
```

## Error Handling
```python
try:
    tracks = client.get_user_recent_tracks("username")
except Exception as e:
    print(f"Error: {e}")
    # Common issues:
    # - Invalid API key
    # - Username not found
    # - Rate limiting
    # - Network issues
```

## Run the Examples
```bash
python example_usage.py
```

## API Limits
- Last.fm has rate limits (typically 5 requests per second)
- Maximum 1000 items per request
- Some data may not be available for all users
- Recent tracks are limited by Last.fm's data retention policy
