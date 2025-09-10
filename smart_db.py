#!/usr/bin/env python3
"""
Smart Last.fm Database - Incremental updates with complete history
Efficiently updates only new scrobbles since last fetch
"""

import json
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import Counter

class SmartLastFMDB:
    def __init__(self, data_file: str = "nnicolema_data/complete_scrobbles.json", 
                 api_key: str = "b50c3e94c0f308ce124052b2e9ecfe3e",
                 username: str = "nnicolema"):
        self.data_file = data_file
        self.api_key = api_key
        self.username = username
        self.scrobbles = self.load_scrobbles()
        self.last_update_file = data_file.replace('.json', '_last_update.txt')
    
    def load_scrobbles(self) -> List[Dict[str, Any]]:
        """Load all scrobbles from the comprehensive JSON file"""
        if not os.path.exists(self.data_file):
            return []
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_scrobbles(self, scrobbles: List[Dict[str, Any]]):
        """Save scrobbles to JSON file"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(scrobbles, f, ensure_ascii=False, indent=2)
    
    def get_last_update_time(self) -> datetime:
        """Get the timestamp of the last update"""
        if os.path.exists(self.last_update_file):
            with open(self.last_update_file, 'r') as f:
                timestamp_str = f.read().strip()
                try:
                    return datetime.fromisoformat(timestamp_str)
                except:
                    pass
        
        # If no last update time, return a very old date to fetch everything
        return datetime(2020, 1, 1)
    
    def save_last_update_time(self, timestamp: datetime):
        """Save the current update timestamp"""
        with open(self.last_update_file, 'w') as f:
            f.write(timestamp.isoformat())
    
    def fetch_new_scrobbles(self, from_timestamp: datetime = None) -> List[Dict[str, Any]]:
        """Fetch new scrobbles from Last.fm API since the given timestamp"""
        if from_timestamp is None:
            from_timestamp = self.get_last_update_time()
        
        print(f"🔄 Fetching new scrobbles since {from_timestamp.strftime('%Y-%m-%d %H:%M:%S')}...")
        
        new_scrobbles = []
        page = 1
        total_pages = 1
        
        while page <= total_pages:
            print(f"📄 Fetching page {page}...")
            
            url = f'http://ws.audioscrobbler.com/2.0/'
            params = {
                'method': 'user.getrecenttracks',
                'user': self.username,
                'api_key': self.api_key,
                'format': 'json',
                'page': page,
                'limit': 1000
            }
            
            try:
                response = requests.get(url, params=params)
                data = response.json()
                
                if 'recenttracks' in data and 'track' in data['recenttracks']:
                    tracks = data['recenttracks']['track']
                    if not isinstance(tracks, list):
                        tracks = [tracks]
                    
                    for track in tracks:
                        scrobble = {
                            'name': track.get('name', ''),
                            'artist': track.get('artist', {}).get('#text', '') if isinstance(track.get('artist'), dict) else track.get('artist', ''),
                            'album': track.get('album', {}).get('#text', '') if isinstance(track.get('album'), dict) else track.get('album', ''),
                            'timestamp': track.get('date', {}).get('#text', '') if isinstance(track.get('date'), dict) else track.get('date', ''),
                            'loved': track.get('loved', '0') == '1',
                            'playcount': int(track.get('playcount', 0)) if track.get('playcount') else 0
                        }
                        
                        # Check if this scrobble is newer than our cutoff
                        if scrobble['timestamp']:
                            try:
                                scrobble_time = datetime.strptime(scrobble['timestamp'], "%d %b %Y, %H:%M")
                                if scrobble_time > from_timestamp:
                                    new_scrobbles.append(scrobble)
                                else:
                                    # We've reached scrobbles older than our cutoff, stop fetching
                                    print(f"✅ Reached cutoff time, stopping fetch")
                                    return new_scrobbles
                            except ValueError:
                                # If we can't parse the timestamp, add it anyway
                                new_scrobbles.append(scrobble)
                        else:
                            # If no timestamp, add it anyway
                            new_scrobbles.append(scrobble)
                    
                    # Get total pages
                    if page == 1:
                        total_pages = int(data['recenttracks'].get('@attr', {}).get('totalPages', 1))
                        print(f"📊 Total pages to check: {total_pages}")
                    
                    page += 1
                else:
                    print('❌ No more tracks found')
                    break
                    
            except Exception as e:
                print(f'❌ Error fetching page {page}: {e}')
                break
        
        print(f"✅ Fetched {len(new_scrobbles)} new scrobbles")
        return new_scrobbles
    
    def update_database(self) -> bool:
        """Update database with new scrobbles efficiently"""
        try:
            print("🔄 Checking for new scrobbles...")
            last_update = self.get_last_update_time()
            new_scrobbles = self.fetch_new_scrobbles(last_update)
            
            if not new_scrobbles:
                print("📭 No new scrobbles found")
                return True
            
            # Merge new scrobbles with existing ones
            # Remove duplicates based on timestamp and track info
            existing_timestamps = set()
            for scrobble in self.scrobbles:
                if scrobble.get('timestamp'):
                    existing_timestamps.add(scrobble['timestamp'])
            
            # Add only truly new scrobbles
            truly_new = []
            for scrobble in new_scrobbles:
                if scrobble.get('timestamp') and scrobble['timestamp'] not in existing_timestamps:
                    truly_new.append(scrobble)
            
            if truly_new:
                # Combine new scrobbles with existing ones
                all_scrobbles = truly_new + self.scrobbles
                
                # Sort by timestamp (newest first)
                def parse_timestamp_for_sort(scrobble):
                    timestamp = scrobble.get('timestamp', '')
                    if not timestamp:
                        return datetime.min
                    try:
                        return datetime.strptime(timestamp, "%d %b %Y, %H:%M")
                    except ValueError:
                        return datetime.min
                
                all_scrobbles.sort(key=parse_timestamp_for_sort, reverse=True)
                
                # Save updated data
                self.save_scrobbles(all_scrobbles)
                self.scrobbles = all_scrobbles
                
                # Update last update time
                self.save_last_update_time(datetime.now())
                
                print(f"📈 Added {len(truly_new)} new scrobbles to database")
                print(f"📊 Total scrobbles now: {len(self.scrobbles):,}")
            else:
                print("📭 No new unique scrobbles to add")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            return False
    
    def get_scrobbles_in_period(self, days: int = None) -> List[Dict[str, Any]]:
        """Get scrobbles within a specific time period"""
        if not self.scrobbles:
            return []
        
        if days is None:
            return self.scrobbles
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filtered_scrobbles = []
        for scrobble in self.scrobbles:
            if scrobble.get('timestamp'):
                try:
                    # Parse timestamp (format: "01 Apr 2023, 03:59")
                    scrobble_date = datetime.strptime(scrobble['timestamp'], "%d %b %Y, %H:%M")
                    if scrobble_date >= cutoff_date:
                        filtered_scrobbles.append(scrobble)
                except ValueError:
                    continue
        
        return filtered_scrobbles
    
    def get_user_stats(self, time_period: str = "overall") -> Dict[str, Any]:
        """Get comprehensive user statistics for any time period"""
        
        # Map time periods to days
        period_mapping = {
            "last_week": 7,
            "last_month": 30,
            "last_3_months": 90,
            "last_6_months": 180,
            "last_year": 365,
            "overall": None
        }
        
        days = period_mapping.get(time_period, None)
        period_scrobbles = self.get_scrobbles_in_period(days)
        
        if not period_scrobbles:
            return {
                "total_plays": 0,
                "unique_tracks": 0,
                "unique_artists": 0,
                "diversity_score": 0.0,
                "top_tracks": [],
                "top_artists": [],
                "top_albums": []
            }
        
        # Calculate basic stats
        total_plays = len(period_scrobbles)
        unique_tracks = len(set(f"{s['artist']} - {s['name']}" for s in period_scrobbles))
        unique_artists = len(set(s['artist'] for s in period_scrobbles))
        diversity_score = unique_tracks / total_plays if total_plays > 0 else 0.0
        
        # Top tracks (by play count)
        track_counts = Counter(f"{s['artist']} - {s['name']}" for s in period_scrobbles)
        top_tracks = [
            {
                "name": track.split(" - ", 1)[1],
                "artist": track.split(" - ", 1)[0],
                "playcount": count
            }
            for track, count in track_counts.most_common(10)
        ]
        
        # Top artists (by play count)
        artist_counts = Counter(s['artist'] for s in period_scrobbles)
        top_artists = [
            {
                "name": artist,
                "playcount": count
            }
            for artist, count in artist_counts.most_common(10)
        ]
        
        # Top albums (by play count)
        album_counts = Counter(f"{s['artist']} - {s['album']}" for s in period_scrobbles if s['album'])
        top_albums = [
            {
                "name": album.split(" - ", 1)[1],
                "artist": album.split(" - ", 1)[0],
                "playcount": count
            }
            for album, count in album_counts.most_common(10)
        ]
        
        return {
            "total_plays": total_plays,
            "unique_tracks": unique_tracks,
            "unique_artists": unique_artists,
            "diversity_score": round(diversity_score, 3),
            "top_tracks": top_tracks,
            "top_artists": top_artists,
            "top_albums": top_albums
        }
    
    def get_recent_tracks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent tracks"""
        return self.scrobbles[:limit]
    
    def search_tracks(self, query: str, days: int = None) -> List[Dict[str, Any]]:
        """Search tracks by artist or song name with aggregated play counts"""
        if days is None:
            # All time search
            period_scrobbles = self.scrobbles
        else:
            period_scrobbles = self.get_scrobbles_in_period(days)
        
        query_lower = query.lower()
        matches = []
        
        for scrobble in period_scrobbles:
            if (query_lower in scrobble.get('name', '').lower() or 
                query_lower in scrobble.get('artist', '').lower()):
                matches.append(scrobble)
        
        # Aggregate matches by track (artist + name combination)
        track_counts = Counter()
        track_data = {}
        
        for match in matches:
            track_key = f"{match.get('artist', '')} - {match.get('name', '')}"
            track_counts[track_key] += 1
            
            # Store the track data (using the first occurrence)
            if track_key not in track_data:
                track_data[track_key] = {
                    'name': match.get('name', ''),
                    'artist': match.get('artist', ''),
                    'album': match.get('album', ''),
                    'timestamp': match.get('timestamp', ''),
                    'loved': match.get('loved', False)
                }
        
        # Convert to list with proper play counts
        result = []
        for track_key, playcount in track_counts.most_common(50):
            track_info = track_data[track_key].copy()
            track_info['playcount'] = playcount
            result.append(track_info)
        
        return result
    
    def get_custom_range_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get user stats for a custom date range"""
        # Filter scrobbles within the date range
        filtered_scrobbles = []
        
        for scrobble in self.scrobbles:
            timestamp_str = scrobble.get('timestamp', '')
            if timestamp_str:
                try:
                    # Parse timestamp: "09 Sep 2025, 22:13"
                    scrobble_date = datetime.strptime(timestamp_str, "%d %b %Y, %H:%M")
                    
                    # Check if within range (inclusive)
                    if start_date.date() <= scrobble_date.date() <= end_date.date():
                        filtered_scrobbles.append(scrobble)
                except ValueError:
                    continue
        
        if not filtered_scrobbles:
            return None
        
        # Count tracks and artists
        track_counts = Counter()
        artist_counts = Counter()
        unique_tracks = set()
        unique_artists = set()
        
        for scrobble in filtered_scrobbles:
            artist = scrobble.get('artist', '')
            track = scrobble.get('name', '')
            
            if artist and track:
                track_key = f"{artist} - {track}"
                track_counts[track_key] += 1
                artist_counts[artist] += 1
                unique_tracks.add(track_key)
                unique_artists.add(artist)
        
        # Build top artists list
        top_artists = []
        for artist, count in artist_counts.most_common(50):
            top_artists.append({
                'name': artist,
                'playcount': count,
                'rank': len(top_artists) + 1
            })
        
        # Build top tracks list
        top_tracks = []
        for track_key, count in track_counts.most_common(50):
            if ' - ' in track_key:
                artist, track_name = track_key.split(' - ', 1)
                top_tracks.append({
                    'name': track_name,
                    'artist': artist,
                    'playcount': count,
                    'rank': len(top_tracks) + 1
                })
        
        # Calculate diversity score
        total_plays = len(filtered_scrobbles)
        diversity_score = len(unique_artists) / max(total_plays, 1)
        
        return {
            'total_plays': total_plays,
            'unique_tracks': len(unique_tracks),
            'unique_artists': len(unique_artists),
            'diversity_score': diversity_score,
            'top_artists': top_artists,
            'top_tracks': top_tracks
        }
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        if not self.scrobbles:
            return {"total_scrobbles": 0, "date_range": "No data"}
        
        timestamps = [s['timestamp'] for s in self.scrobbles if s.get('timestamp')]
        if timestamps:
            timestamps.sort()
            return {
                "total_scrobbles": len(self.scrobbles),
                "oldest_scrobble": timestamps[0],
                "newest_scrobble": timestamps[-1],
                "date_range": f"{timestamps[0]} to {timestamps[-1]}",
                "last_updated": self.get_last_update_time().strftime('%Y-%m-%d %H:%M:%S'),
                "efficient_updates": True
            }
        
        return {"total_scrobbles": len(self.scrobbles), "date_range": "No timestamps"}

# Global instance
smart_db = SmartLastFMDB()
