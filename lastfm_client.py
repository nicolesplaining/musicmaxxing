"""
Last.fm API Client with Time-Based Querying
Provides functionality to query user statistics for specific time periods
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass


@dataclass
class TimeRange:
    """Represents a time range for querying Last.fm data"""
    start_date: datetime
    end_date: datetime
    
    def to_timestamp(self) -> Tuple[int, int]:
        """Convert to Unix timestamps for API calls"""
        return int(self.start_date.timestamp()), int(self.end_date.timestamp())
    
    @classmethod
    def from_days_ago(cls, days: int) -> 'TimeRange':
        """Create a time range from N days ago to now"""
        end = datetime.now()
        start = end - timedelta(days=days)
        return cls(start, end)
    
    @classmethod
    def from_weeks_ago(cls, weeks: int) -> 'TimeRange':
        """Create a time range from N weeks ago to now"""
        end = datetime.now()
        start = end - timedelta(weeks=weeks)
        return cls(start, end)
    
    @classmethod
    def from_months_ago(cls, months: int) -> 'TimeRange':
        """Create a time range from N months ago to now"""
        end = datetime.now()
        start = end - timedelta(days=months * 30)  # Approximate
        return cls(start, end)
    
    @classmethod
    def from_years_ago(cls, years: int) -> 'TimeRange':
        """Create a time range from N years ago to now"""
        end = datetime.now()
        start = end - timedelta(days=years * 365)  # Approximate
        return cls(start, end)


@dataclass
class TrackInfo:
    """Represents track information from Last.fm"""
    name: str
    artist: str
    album: Optional[str] = None
    playcount: int = 0
    timestamp: Optional[datetime] = None
    loved: bool = False


@dataclass
class ArtistInfo:
    """Represents artist information from Last.fm"""
    name: str
    playcount: int
    rank: int
    url: Optional[str] = None


@dataclass
class AlbumInfo:
    """Represents album information from Last.fm"""
    name: str
    artist: str
    playcount: int
    rank: int
    url: Optional[str] = None


class LastFMClient:
    """Last.fm API client with time-based querying capabilities"""
    
    BASE_URL = "http://ws.audioscrobbler.com/2.0/"
    
    def __init__(self, api_key: str, user_agent: str = "VibeRL/1.0"):
        """
        Initialize the Last.fm client
        
        Args:
            api_key: Your Last.fm API key
            user_agent: User agent string for requests
        """
        self.api_key = api_key
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent
        })
    
    def _make_request(self, method: str, params: Dict[str, str]) -> Dict:
        """Make a request to the Last.fm API"""
        params.update({
            'method': method,
            'api_key': self.api_key,
            'format': 'json'
        })
        
        try:
            response = self.session.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {e}")
    
    def get_user_recent_tracks(
        self, 
        username: str, 
        time_range: Optional[TimeRange] = None,
        limit: int = 50,
        page: int = 1
    ) -> List[TrackInfo]:
        """
        Get user's recent tracks within a time range
        
        Args:
            username: Last.fm username
            time_range: Time range to query (if None, gets all recent tracks)
            limit: Number of tracks to return per page (max 1000)
            page: Page number to retrieve
            
        Returns:
            List of TrackInfo objects
        """
        params = {
            'user': username,
            'limit': str(min(limit, 1000)),
            'page': str(page)
        }
        
        if time_range:
            start_ts, end_ts = time_range.to_timestamp()
            params['from'] = str(start_ts)
            params['to'] = str(end_ts)
        
        data = self._make_request('user.getrecenttracks', params)
        
        tracks = []
        if 'recenttracks' in data and 'track' in data['recenttracks']:
            for track_data in data['recenttracks']['track']:
                # Handle both single track and list of tracks
                if isinstance(track_data, list):
                    track_data = track_data[0]
                
                track = TrackInfo(
                    name=track_data.get('name', ''),
                    artist=track_data.get('artist', {}).get('#text', ''),
                    album=track_data.get('album', {}).get('#text'),
                    playcount=int(track_data.get('playcount', 0)),
                    loved=track_data.get('loved') == '1'
                )
                
                # Parse timestamp if available
                if 'date' in track_data and 'uts' in track_data['date']:
                    track.timestamp = datetime.fromtimestamp(int(track_data['date']['uts']))
                
                tracks.append(track)
        
        return tracks
    
    def get_user_top_tracks(
        self, 
        username: str, 
        time_range: Optional[TimeRange] = None,
        period: str = 'overall',
        limit: int = 50
    ) -> List[TrackInfo]:
        """
        Get user's top tracks within a time range
        
        Args:
            username: Last.fm username
            time_range: Time range to query (if None, uses period parameter)
            period: Time period ('overall', '7day', '1month', '3month', '6month', '12month')
            limit: Number of tracks to return (max 1000)
            
        Returns:
            List of TrackInfo objects
        """
        params = {
            'user': username,
            'period': period,
            'limit': str(min(limit, 1000))
        }
        
        if time_range:
            start_ts, end_ts = time_range.to_timestamp()
            params['from'] = str(start_ts)
            params['to'] = str(end_ts)
        
        data = self._make_request('user.gettoptracks', params)
        
        tracks = []
        if 'toptracks' in data and 'track' in data['toptracks']:
            for i, track_data in enumerate(data['toptracks']['track']):
                track = TrackInfo(
                    name=track_data.get('name', ''),
                    artist=track_data.get('artist', {}).get('name', ''),
                    playcount=int(track_data.get('playcount', 0)),
                    rank=i + 1
                )
                tracks.append(track)
        
        return tracks
    
    def get_user_top_artists(
        self, 
        username: str, 
        time_range: Optional[TimeRange] = None,
        period: str = 'overall',
        limit: int = 50
    ) -> List[ArtistInfo]:
        """
        Get user's top artists within a time range
        
        Args:
            username: Last.fm username
            time_range: Time range to query (if None, uses period parameter)
            period: Time period ('overall', '7day', '1month', '3month', '3month', '6month', '12month')
            limit: Number of artists to return (max 1000)
            
        Returns:
            List of ArtistInfo objects
        """
        params = {
            'user': username,
            'period': period,
            'limit': str(min(limit, 1000))
        }
        
        if time_range:
            start_ts, end_ts = time_range.to_timestamp()
            params['from'] = str(start_ts)
            params['to'] = str(end_ts)
        
        data = self._make_request('user.gettopartists', params)
        
        artists = []
        if 'topartists' in data and 'artist' in data['topartists']:
            for i, artist_data in enumerate(data['topartists']['artist']):
                artist = ArtistInfo(
                    name=artist_data.get('name', ''),
                    playcount=int(artist_data.get('playcount', 0)),
                    rank=i + 1,
                    url=artist_data.get('url')
                )
                artists.append(artist)
        
        return artists
    
    def get_user_top_albums(
        self, 
        username: str, 
        time_range: Optional[TimeRange] = None,
        period: str = 'overall',
        limit: int = 50
    ) -> List[AlbumInfo]:
        """
        Get user's top albums within a time range
        
        Args:
            username: Last.fm username
            time_range: Time range to query (if None, uses period parameter)
            period: Time period ('overall', '7day', '1month', '3month', '6month', '12month')
            limit: Number of albums to return (max 1000)
            
        Returns:
            List of AlbumInfo objects
        """
        params = {
            'user': username,
            'period': period,
            'limit': str(min(limit, 1000))
        }
        
        if time_range:
            start_ts, end_ts = time_range.to_timestamp()
            params['from'] = str(start_ts)
            params['to'] = str(end_ts)
        
        data = self._make_request('user.gettopalbums', params)
        
        albums = []
        if 'topalbums' in data and 'album' in data['topalbums']:
            for i, album_data in enumerate(data['topalbums']['album']):
                album = AlbumInfo(
                    name=album_data.get('name', ''),
                    artist=album_data.get('artist', {}).get('name', ''),
                    playcount=int(album_data.get('playcount', 0)),
                    rank=i + 1,
                    url=album_data.get('url')
                )
                albums.append(album)
        
        return albums
    
    def get_user_stats(
        self, 
        username: str, 
        time_range: Optional[TimeRange] = None
    ) -> Dict[str, Union[int, List[TrackInfo], List[ArtistInfo], List[AlbumInfo]]]:
        """
        Get comprehensive user statistics for a time period
        
        Args:
            username: Last.fm username
            time_range: Time range to query (if None, gets overall stats)
            
        Returns:
            Dictionary containing various statistics
        """
        stats = {}
        
        # Get recent tracks to calculate total plays in period
        recent_tracks = self.get_user_recent_tracks(username, time_range, limit=1000)
        stats['total_plays'] = sum(track.playcount for track in recent_tracks)
        stats['unique_tracks'] = len(set(f"{track.artist} - {track.name}" for track in recent_tracks))
        
        # Get top tracks, artists, and albums
        stats['top_tracks'] = self.get_user_top_tracks(username, time_range, limit=20)
        stats['top_artists'] = self.get_user_top_artists(username, time_range, limit=20)
        stats['top_albums'] = self.get_user_top_albums(username, time_range, limit=20)
        
        # Calculate listening diversity
        unique_artists = len(set(track.artist for track in recent_tracks))
        stats['unique_artists'] = unique_artists
        stats['diversity_score'] = unique_artists / max(len(recent_tracks), 1)
        
        return stats
    
    def get_user_weekly_chart(
        self, 
        username: str, 
        from_date: datetime, 
        to_date: datetime
    ) -> Dict[str, List]:
        """
        Get user's weekly chart for a specific date range
        
        Args:
            username: Last.fm username
            from_date: Start date
            to_date: End date
            
        Returns:
            Dictionary containing weekly chart data
        """
        time_range = TimeRange(from_date, to_date)
        
        return {
            'tracks': self.get_user_top_tracks(username, time_range, limit=100),
            'artists': self.get_user_top_artists(username, time_range, limit=100),
            'albums': self.get_user_top_albums(username, time_range, limit=100)
        }
    
    def search_user_activity(
        self, 
        username: str, 
        query: str, 
        time_range: Optional[TimeRange] = None
    ) -> List[TrackInfo]:
        """
        Search for specific tracks/artists in user's listening history
        
        Args:
            username: Last.fm username
            query: Search query (track name or artist)
            time_range: Time range to search within
            
        Returns:
            List of matching TrackInfo objects
        """
        recent_tracks = self.get_user_recent_tracks(username, time_range, limit=1000)
        
        # Filter tracks that match the query
        query_lower = query.lower()
        matching_tracks = [
            track for track in recent_tracks
            if query_lower in track.name.lower() or query_lower in track.artist.lower()
        ]
        
        return matching_tracks


# Example usage and utility functions
def create_time_ranges() -> Dict[str, TimeRange]:
    """Create common time ranges for easy access"""
    return {
        'last_week': TimeRange.from_days_ago(7),
        'last_month': TimeRange.from_days_ago(30),
        'last_3_months': TimeRange.from_days_ago(90),
        'last_6_months': TimeRange.from_days_ago(180),
        'last_year': TimeRange.from_days_ago(365),
        'this_year': TimeRange(
            start_date=datetime(datetime.now().year, 1, 1),
            end_date=datetime.now()
        ),
        'last_year_full': TimeRange(
            start_date=datetime(datetime.now().year - 1, 1, 1),
            end_date=datetime(datetime.now().year - 1, 12, 31)
        )
    }


def format_stats_summary(stats: Dict) -> str:
    """Format user stats into a readable summary"""
    summary = f"""
User Statistics Summary:
- Total Plays: {stats.get('total_plays', 0):,}
- Unique Tracks: {stats.get('unique_tracks', 0):,}
- Unique Artists: {stats.get('unique_artists', 0):,}
- Diversity Score: {stats.get('diversity_score', 0):.2%}

Top Artists:
"""
    
    for i, artist in enumerate(stats.get('top_artists', [])[:5], 1):
        summary += f"{i}. {artist.name} ({artist.playcount:,} plays)\n"
    
    summary += "\nTop Tracks:\n"
    for i, track in enumerate(stats.get('top_tracks', [])[:5], 1):
        summary += f"{i}. {track.artist} - {track.name} ({track.playcount:,} plays)\n"
    
    return summary
