#!/usr/bin/env python3
"""
Advanced Analytics for Last.fm Data
Unlimited analytics since we have complete JSON database
"""

import json
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
import calendar

class AdvancedAnalytics:
    def __init__(self, data_file: str = "nnicolema_data/complete_scrobbles.json", 
                 api_key: str = "b50c3e94c0f308ce124052b2e9ecfe3e",
                 username: str = "nnicolema"):
        self.data_file = data_file
        self.api_key = api_key
        self.username = username
        self.scrobbles = self.load_scrobbles()
        self.last_update_file = data_file.replace('.json', '_last_update.txt')
    
    def load_scrobbles(self) -> List[Dict[str, Any]]:
        """Load all scrobbles from JSON file"""
        if not os.path.exists(self.data_file):
            return []
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def reload_scrobbles(self):
        """Reload scrobbles from disk (useful after external updates)"""
        self.scrobbles = self.load_scrobbles()
    
    def parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse Last.fm timestamp format"""
        try:
            return datetime.strptime(timestamp_str, "%d %b %Y, %H:%M")
        except ValueError:
            return datetime.min
    
    def get_scrobbles_in_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get scrobbles within a custom date range"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include end date
        
        filtered_scrobbles = []
        for scrobble in self.scrobbles:
            if scrobble.get('timestamp'):
                scrobble_dt = self.parse_timestamp(scrobble['timestamp'])
                if start_dt <= scrobble_dt < end_dt:
                    filtered_scrobbles.append(scrobble)
        
        return filtered_scrobbles
    
    def get_yearly_breakdown(self) -> Dict[str, Any]:
        """Get listening stats broken down by year"""
        yearly_data = defaultdict(list)
        
        for scrobble in self.scrobbles:
            if scrobble.get('timestamp'):
                scrobble_dt = self.parse_timestamp(scrobble['timestamp'])
                year = scrobble_dt.year
                yearly_data[year].append(scrobble)
        
        yearly_stats = {}
        for year, scrobbles in yearly_data.items():
            yearly_stats[str(year)] = self.calculate_period_stats(scrobbles)
        
        return yearly_stats
    
    def get_monthly_breakdown(self, year: int = None) -> Dict[str, Any]:
        """Get listening stats broken down by month"""
        if year is None:
            year = datetime.now().year
        
        monthly_data = defaultdict(list)
        
        for scrobble in self.scrobbles:
            if scrobble.get('timestamp'):
                scrobble_dt = self.parse_timestamp(scrobble['timestamp'])
                if scrobble_dt.year == year:
                    month = scrobble_dt.month
                    monthly_data[month].append(scrobble)
        
        monthly_stats = {}
        for month, scrobbles in monthly_data.items():
            month_name = calendar.month_name[month]
            monthly_stats[month_name] = self.calculate_period_stats(scrobbles)
        
        return monthly_stats
    
    def get_listening_patterns(self) -> Dict[str, Any]:
        """Analyze listening patterns by time of day and day of week"""
        hourly_counts = defaultdict(int)
        daily_counts = defaultdict(int)
        hourly_by_day = defaultdict(lambda: defaultdict(int))
        
        for scrobble in self.scrobbles:
            if scrobble.get('timestamp'):
                scrobble_dt = self.parse_timestamp(scrobble['timestamp'])
                hour = scrobble_dt.hour
                day_of_week = scrobble_dt.strftime('%A')
                
                hourly_counts[hour] += 1
                daily_counts[day_of_week] += 1
                hourly_by_day[day_of_week][hour] += 1
        
        # Convert to sorted lists
        hourly_data = [{'hour': h, 'count': c} for h, c in sorted(hourly_counts.items())]
        daily_data = [{'day': d, 'count': c} for d, c in sorted(daily_counts.items(), 
                      key=lambda x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(x[0]))]
        
        return {
            'hourly_distribution': hourly_data,
            'daily_distribution': daily_data,
            'hourly_by_day': dict(hourly_by_day)
        }
    
    def get_artist_evolution(self, artist_name: str, period_months: int = 6) -> Dict[str, Any]:
        """Track how an artist's popularity changes over time"""
        artist_scrobbles = [s for s in self.scrobbles if s.get('artist', '').lower() == artist_name.lower()]
        
        if not artist_scrobbles:
            return {'error': f'No scrobbles found for artist: {artist_name}'}
        
        # Group by time periods
        period_data = defaultdict(list)
        
        for scrobble in artist_scrobbles:
            if scrobble.get('timestamp'):
                scrobble_dt = self.parse_timestamp(scrobble['timestamp'])
                period_key = f"{scrobble_dt.year}-{scrobble_dt.month:02d}"
                period_data[period_key].append(scrobble)
        
        evolution = []
        for period, scrobbles in sorted(period_data.items()):
            evolution.append({
                'period': period,
                'count': len(scrobbles),
                'unique_tracks': len(set(f"{s['name']} - {s['artist']}" for s in scrobbles)),
                'top_track': Counter(s['name'] for s in scrobbles).most_common(1)[0] if scrobbles else None
            })
        
        return {
            'artist': artist_name,
            'total_scrobbles': len(artist_scrobbles),
            'evolution': evolution
        }
    
    def get_comparative_analytics(self, period1_start: str, period1_end: str, 
                                 period2_start: str, period2_end: str) -> Dict[str, Any]:
        """Compare two time periods"""
        period1_scrobbles = self.get_scrobbles_in_range(period1_start, period1_end)
        period2_scrobbles = self.get_scrobbles_in_range(period2_start, period2_end)
        
        period1_stats = self.calculate_period_stats(period1_scrobbles)
        period2_stats = self.calculate_period_stats(period2_scrobbles)
        
        # Calculate changes
        changes = {}
        for key in ['total_plays', 'unique_tracks', 'unique_artists']:
            if key in period1_stats and key in period2_stats:
                old_val = period1_stats[key]
                new_val = period2_stats[key]
                if old_val > 0:
                    changes[key] = {
                        'absolute': new_val - old_val,
                        'percentage': round(((new_val - old_val) / old_val) * 100, 1)
                    }
                else:
                    changes[key] = {'absolute': new_val, 'percentage': 100}
        
        return {
            'period1': {
                'range': f"{period1_start} to {period1_end}",
                'stats': period1_stats
            },
            'period2': {
                'range': f"{period2_start} to {period2_end}",
                'stats': period2_stats
            },
            'changes': changes
        }
    
    def get_seasonal_analysis(self) -> Dict[str, Any]:
        """Analyze listening patterns by season"""
        seasonal_data = defaultdict(list)
        
        for scrobble in self.scrobbles:
            if scrobble.get('timestamp'):
                scrobble_dt = self.parse_timestamp(scrobble['timestamp'])
                month = scrobble_dt.month
                
                if month in [12, 1, 2]:
                    season = 'Winter'
                elif month in [3, 4, 5]:
                    season = 'Spring'
                elif month in [6, 7, 8]:
                    season = 'Summer'
                else:
                    season = 'Fall'
                
                seasonal_data[season].append(scrobble)
        
        seasonal_stats = {}
        for season, scrobbles in seasonal_data.items():
            seasonal_stats[season] = self.calculate_period_stats(scrobbles)
        
        return seasonal_stats
    
    def get_top_periods(self, metric: str = 'total_plays', period_type: str = 'month') -> List[Dict[str, Any]]:
        """Get top periods by any metric"""
        if period_type == 'month':
            period_data = defaultdict(list)
            for scrobble in self.scrobbles:
                if scrobble.get('timestamp'):
                    scrobble_dt = self.parse_timestamp(scrobble['timestamp'])
                    period_key = f"{scrobble_dt.year}-{scrobble_dt.month:02d}"
                    period_data[period_key].append(scrobble)
        elif period_type == 'year':
            period_data = defaultdict(list)
            for scrobble in self.scrobbles:
                if scrobble.get('timestamp'):
                    scrobble_dt = self.parse_timestamp(scrobble['timestamp'])
                    period_key = str(scrobble_dt.year)
                    period_data[period_key].append(scrobble)
        else:
            return []
        
        period_stats = []
        for period, scrobbles in period_data.items():
            stats = self.calculate_period_stats(scrobbles)
            stats['period'] = period
            period_stats.append(stats)
        
        return sorted(period_stats, key=lambda x: x.get(metric, 0), reverse=True)[:10]
    
    def get_shoegaze_analytics(self) -> Dict[str, Any]:
        """Get focused shoegaze-specific analytics (actual shoegaze + international variations)"""
        # Define focused shoegaze artists (actual shoegaze + international variations)
        shoegaze_artists = {
            # Classic Shoegaze (UK/US)
            'my bloody valentine', 'slowdive', 'ride', 'lush', 'cocteau twins',
            'pale saints', 'chapterhouse', 'swervedriver', 'curve', 'moose',
            'drop nineteens', 'verve', 'spiritualized', 'spacemen 3', 'galaxie 500',
            'mazzy star', 'beach house', 'deerhunter', 'wild nothing',
            'tame impala', 'beach fossils', 'craft spells', 'diiiv', 'alvvays',
            'pity sex', 'nothing', 'whirr', 'ringo deathstarr', 'pinkshinyultrablast',
            'tamaryn', 'candy claws',
            
            # Dream pop artists
            'beach house', 'mazzy star', 'cocteau twins', 'galaxie 500',
            'slowdive', 'lush', 'pale saints', 'chapterhouse', 'verve',
            'spiritualized', 'spacemen 3', 'wild nothing', 'craft spells',
            'diiiv', 'alvvays', 'tamaryn', 'candy claws',
            
            # Noise pop artists
            'my bloody valentine', 'swervedriver', 'curve', 'moose',
            'drop nineteens', 'pity sex', 'nothing', 'whirr', 'ringo deathstarr',
            'pinkshinyultrablast', 'tamaryn', 'candy claws',
            
            # Post-rock artists with shoegaze elements
            'explosions in the sky', 'godspeed you! black emperor', 'mogwai',
            'sigur rós', 'tortoise', 'stereolab', 'broadcast', 'four tet',
            'boards of canada', 'aphex twin', 'autechre', 'tim hecker',
            'grouper', 'julianna barwick', 'helen', 'jessica pratt',
            
            # Indie rock with shoegaze elements
            'arcade fire', 'interpol', 'the national', 'grizzly bear',
            'fleet foxes', 'bon iver', 'sufjan stevens', 'iron & wine',
            'cat power', 'feist', 'st. vincent', 'angel olsen',
            'sharon van etten', 'julia holter', 'weyes blood', 'big thief',
            
            # Psychedelic rock with shoegaze elements
            'tame impala', 'pond', 'king gizzard & the lizard wizard',
            'thee oh sees', 'ty segall', 'white fence', 'mild high club',
            'melody\'s echo chamber', 'temples', 'the babe rainbow',
            'kikagaku moyo', 'goat', 'wooden shjips', 'moon duo',
            
            # Space rock artists
            'spiritualized', 'spacemen 3', 'galaxie 500', 'mazzy star',
            'slowdive', 'lush', 'pale saints', 'chapterhouse', 'verve',
            'spiritualized', 'spacemen 3', 'galaxie 500', 'mazzy star',
            
            # Ambient artists with shoegaze elements
            'boards of canada', 'aphex twin', 'autechre', 'tim hecker',
            'grouper', 'julianna barwick', 'helen', 'jessica pratt',
            'max richter', 'olafur arnalds', 'nils frahm', 'ludovico einaudi',
            
            # Blackgaze artists
            'alcest', 'deafheaven', 'wolves in the throne room', 'agalloch',
            'les discrets', 'sylvaine', 'heretoir', 'woods of desolation',
            'gris', 'sadness', 'coldworld', 'germ', 'sadness',
            
            # Nu gaze artists
            'diiiv', 'alvvays', 'tamaryn', 'candy claws', 'pity sex',
            'nothing', 'whirr', 'ringo deathstarr', 'pinkshinyultrablast',
            'tamaryn', 'candy claws', 'craft spells', 'beach fossils',
            'wild nothing', 'tame impala', 'beach house', 'deerhunter',
            
            # Indie shoegaze artists
            'my bloody valentine', 'slowdive', 'ride', 'lush', 'cocteau twins',
            'pale saints', 'chapterhouse', 'swervedriver', 'curve', 'moose',
            'drop nineteens', 'verve', 'spiritualized', 'spacemen 3', 'galaxie 500',
            'mazzy star', 'beach house', 'deerhunter', 'wild nothing',
            'tame impala', 'beach fossils', 'craft spells', 'diiiv', 'alvvays',
            'pity sex', 'nothing', 'whirr', 'ringo deathstarr', 'pinkshinyultrablast',
            'tamaryn', 'candy claws', 'tamaryn', 'candy claws',
            
            # Post-punk with shoegaze elements
            'joy division', 'new order', 'the cure', 'siouxsie and the banshees',
            'echo & the bunnymen', 'tears for fears', 'depeche mode',
            'the smiths', 'the jesus and mary chain', 'primal scream',
            'my bloody valentine', 'slowdive', 'ride', 'lush', 'cocteau twins',
            
            # Noise rock with shoegaze elements
            'sonic youth', 'dinosaur jr.', 'pixies', 'hüsker dü', 'fugazi',
            'my bloody valentine', 'swervedriver', 'curve', 'moose',
            'drop nineteens', 'pity sex', 'nothing', 'whirr', 'ringo deathstarr',
            'pinkshinyultrablast', 'tamaryn', 'candy claws',
            
            # International Shoegaze - Chinese
            'carsick cars', 'p.k.14', 'rebuilding the rights of statues', 'snapline',
            'penguin cafe', 'the gar', 'avokado', 'the flowers', 'carsick cars',
            'p.k.14', 'rebuilding the rights of statues', 'snapline', 'penguin cafe',
            'the gar', 'avokado', 'the flowers', 'carsick cars', 'p.k.14',
            
            # International Shoegaze - Korean
            'parannoul', 'asian glow', 'sonagi', 'wave to earth', 'se so neon',
            'hyukoh', 'the black skirts', '10cm', 'bol4', 'iu', 'heize',
            'parannoul', 'asian glow', 'sonagi', 'wave to earth', 'se so neon',
            'hyukoh', 'the black skirts', '10cm', 'bol4', 'iu', 'heize',
            
            # International Shoegaze - Japanese
            'kinoko teikoku', 'mass of the fermenting dregs', 'tricot', 'polysics',
            'the pillows', 'l\'arc~en~ciel', 'dir en grey', 'x japan', 'luna sea',
            'glay', 'b\'z', 'mr. children', 'southern all stars', 'smap',
            'kinoko teikoku', 'mass of the fermenting dregs', 'tricot', 'polysics',
            'the pillows', 'l\'arc~en~ciel', 'dir en grey', 'x japan', 'luna sea',
            
            # International Shoegaze - European
            'alcest', 'les discrets', 'sylvaine', 'heretoir', 'agalloch',
            'wolves in the throne room', 'deafheaven', 'gris', 'sadness',
            'coldworld', 'germ', 'sadness', 'alcest', 'les discrets',
            'sylvaine', 'heretoir', 'agalloch', 'wolves in the throne room',
            
            # International Shoegaze - Latin American
            'los planetas', 'vetusta morla', 'los punsetes', 'los campesinos!',
            'carlos sadness', 'vetusta morla', 'los punsetes', 'los campesinos!',
            'carlos sadness', 'vetusta morla', 'los punsetes', 'los campesinos!',
            
            # International Shoegaze - Other Asian
            'parannoul', 'asian glow', 'sonagi', 'wave to earth', 'se so neon',
            'hyukoh', 'the black skirts', '10cm', 'bol4', 'iu', 'heize',
            'parannoul', 'asian glow', 'sonagi', 'wave to earth', 'se so neon',
            
            # International Shoegaze - Australian/New Zealand
            'tame impala', 'pond', 'king gizzard & the lizard wizard', 'thee oh sees',
            'ty segall', 'white fence', 'mild high club', 'melody\'s echo chamber',
            'temples', 'the babe rainbow', 'kikagaku moyo', 'goat', 'wooden shjips',
            'moon duo', 'tame impala', 'pond', 'king gizzard & the lizard wizard',
            
            # International Shoegaze - Canadian
            'alvvays', 'tamaryn', 'candy claws', 'craft spells', 'beach fossils',
            'wild nothing', 'tame impala', 'beach house', 'deerhunter', 'alvvays',
            'tamaryn', 'candy claws', 'craft spells', 'beach fossils', 'wild nothing',
            
            # International Shoegaze - Scandinavian
            'sigur rós', 'múm', 'björk', 'the knife', 'fever ray', 'lykke li',
            'first aid kit', 'of monsters and men', 'sigur rós', 'múm', 'björk',
            'the knife', 'fever ray', 'lykke li', 'first aid kit', 'of monsters and men',
            
            # International Shoegaze - Eastern European
            'sigur rós', 'múm', 'björk', 'the knife', 'fever ray', 'lykke li',
            'first aid kit', 'of monsters and men', 'sigur rós', 'múm', 'björk',
            'the knife', 'fever ray', 'lykke li', 'first aid kit', 'of monsters and men'
        }
        
        # Focused shoegaze keywords
        shoegaze_keywords = {
            # Core shoegaze terms
            'shoegaze', 'dream pop', 'noise pop', 'indie shoegaze',
            'ethereal', 'ambient', 'atmospheric', 'reverb', 'delay',
            'fuzz', 'distortion', 'wall of sound', 'melancholic',
            'dreamy', 'hazy', 'washed out',
            
            # International shoegaze terms
            'chinese shoegaze', 'korean shoegaze', 'japanese shoegaze',
            'asian shoegaze', 'european shoegaze', 'latin shoegaze',
            'scandinavian shoegaze', 'australian shoegaze', 'canadian shoegaze',
            'international shoegaze', 'world shoegaze', 'global shoegaze',
            
            # Shoegaze subgenres
            'blackgaze', 'nu gaze', 'slowcore', 'space rock'
        }
        
        # Filter shoegaze scrobbles
        shoegaze_scrobbles = []
        for scrobble in self.scrobbles:
            artist = scrobble.get('artist', '').lower()
            track = scrobble.get('name', '').lower()
            album = scrobble.get('album', '').lower()
            
            # Check if artist is known shoegaze
            if any(sg_artist in artist for sg_artist in shoegaze_artists):
                shoegaze_scrobbles.append(scrobble)
            # Check if track/album contains shoegaze keywords
            elif any(keyword in track or keyword in album for keyword in shoegaze_keywords):
                shoegaze_scrobbles.append(scrobble)
        
        if not shoegaze_scrobbles:
            return {
                'total_shoegaze_plays': 0,
                'shoegaze_percentage': 0.0,
                'top_shoegaze_artists': [],
                'top_shoegaze_tracks': [],
                'shoegaze_evolution': [],
                'shoegaze_seasonal': {},
                'shoegaze_patterns': {}
            }
        
        # Calculate basic stats
        total_plays = len(self.scrobbles)
        shoegaze_plays = len(shoegaze_scrobbles)
        shoegaze_percentage = (shoegaze_plays / total_plays * 100) if total_plays > 0 else 0
        
        # Top shoegaze artists
        artist_counts = Counter(s['artist'] for s in shoegaze_scrobbles)
        top_shoegaze_artists = [
            {'name': artist, 'playcount': count, 'percentage': round(count / shoegaze_plays * 100, 1)}
            for artist, count in artist_counts.most_common(15)
        ]
        
        # Top shoegaze tracks
        track_counts = Counter(f"{s['artist']} - {s['name']}" for s in shoegaze_scrobbles)
        top_shoegaze_tracks = [
            {
                'name': track.split(" - ", 1)[1],
                'artist': track.split(" - ", 1)[0],
                'playcount': count,
                'percentage': round(count / shoegaze_plays * 100, 1)
            }
            for track, count in track_counts.most_common(20)
        ]
        
        # Shoegaze evolution over time
        shoegaze_evolution = self._get_shoegaze_evolution(shoegaze_scrobbles)
        
        # Seasonal shoegaze patterns
        shoegaze_seasonal = self._get_shoegaze_seasonal(shoegaze_scrobbles)
        
        # Shoegaze listening patterns
        shoegaze_patterns = self._get_shoegaze_patterns(shoegaze_scrobbles)
        
        return {
            'total_shoegaze_plays': shoegaze_plays,
            'shoegaze_percentage': round(shoegaze_percentage, 1),
            'total_plays': total_plays,
            'top_shoegaze_artists': top_shoegaze_artists,
            'top_shoegaze_tracks': top_shoegaze_tracks,
            'shoegaze_evolution': shoegaze_evolution,
            'shoegaze_seasonal': shoegaze_seasonal,
            'shoegaze_patterns': shoegaze_patterns
        }
    
    def _get_shoegaze_evolution(self, shoegaze_scrobbles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Track shoegaze listening evolution over time"""
        monthly_data = defaultdict(list)
        
        for scrobble in shoegaze_scrobbles:
            if scrobble.get('timestamp'):
                scrobble_dt = self.parse_timestamp(scrobble['timestamp'])
                month_key = f"{scrobble_dt.year}-{scrobble_dt.month:02d}"
                monthly_data[month_key].append(scrobble)
        
        evolution = []
        for month, scrobbles in sorted(monthly_data.items()):
            artist_counts = Counter(s['artist'] for s in scrobbles)
            top_artist = artist_counts.most_common(1)[0] if artist_counts else ('Unknown', 0)
            
            evolution.append({
                'period': month,
                'plays': len(scrobbles),
                'unique_artists': len(artist_counts),
                'top_artist': top_artist[0],
                'top_artist_plays': top_artist[1]
            })
        
        return evolution
    
    def _get_shoegaze_seasonal(self, shoegaze_scrobbles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get seasonal patterns for shoegaze listening"""
        seasonal_data = defaultdict(list)
        
        for scrobble in shoegaze_scrobbles:
            if scrobble.get('timestamp'):
                scrobble_dt = self.parse_timestamp(scrobble['timestamp'])
                month = scrobble_dt.month
                
                if month in [12, 1, 2]:
                    season = 'Winter'
                elif month in [3, 4, 5]:
                    season = 'Spring'
                elif month in [6, 7, 8]:
                    season = 'Summer'
                else:
                    season = 'Fall'
                
                seasonal_data[season].append(scrobble)
        
        seasonal_stats = {}
        for season, scrobbles in seasonal_data.items():
            artist_counts = Counter(s['artist'] for s in scrobbles)
            seasonal_stats[season] = {
                'plays': len(scrobbles),
                'unique_artists': len(artist_counts),
                'top_artist': artist_counts.most_common(1)[0] if artist_counts else ('Unknown', 0)
            }
        
        return seasonal_stats
    
    def _get_shoegaze_patterns(self, shoegaze_scrobbles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get listening patterns specific to shoegaze"""
        hourly_counts = defaultdict(int)
        daily_counts = defaultdict(int)
        
        for scrobble in shoegaze_scrobbles:
            if scrobble.get('timestamp'):
                scrobble_dt = self.parse_timestamp(scrobble['timestamp'])
                hour = scrobble_dt.hour
                day_of_week = scrobble_dt.strftime('%A')
                
                hourly_counts[hour] += 1
                daily_counts[day_of_week] += 1
        
        # Find peak times
        peak_hour = max(hourly_counts.items(), key=lambda x: x[1]) if hourly_counts else (0, 0)
        peak_day = max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else ('Monday', 0)
        
        return {
            'hourly_distribution': [{'hour': h, 'count': c} for h, c in sorted(hourly_counts.items())],
            'daily_distribution': [{'day': d, 'count': c} for d, c in sorted(daily_counts.items(), 
                              key=lambda x: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(x[0]))],
            'peak_hour': peak_hour[0],
            'peak_day': peak_day[0],
            'peak_hour_plays': peak_hour[1],
            'peak_day_plays': peak_day[1]
        }

    def calculate_period_stats(self, scrobbles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive stats for a period"""
        if not scrobbles:
            return {
                'total_plays': 0,
                'unique_tracks': 0,
                'unique_artists': 0,
                'diversity_score': 0.0,
                'top_tracks': [],
                'top_artists': [],
                'top_albums': []
            }
        
        total_plays = len(scrobbles)
        unique_tracks = len(set(f"{s['artist']} - {s['name']}" for s in scrobbles))
        unique_artists = len(set(s['artist'] for s in scrobbles))
        diversity_score = unique_tracks / total_plays if total_plays > 0 else 0.0
        
        # Top tracks
        track_counts = Counter(f"{s['artist']} - {s['name']}" for s in scrobbles)
        top_tracks = [
            {
                'name': track.split(" - ", 1)[1],
                'artist': track.split(" - ", 1)[0],
                'playcount': count
            }
            for track, count in track_counts.most_common(10)
        ]
        
        # Top artists
        artist_counts = Counter(s['artist'] for s in scrobbles)
        top_artists = [
            {
                'name': artist,
                'playcount': count
            }
            for artist, count in artist_counts.most_common(10)
        ]
        
        # Top albums
        album_counts = Counter(f"{s['artist']} - {s['album']}" for s in scrobbles if s['album'])
        top_albums = [
            {
                'name': album.split(" - ", 1)[1],
                'artist': album.split(" - ", 1)[0],
                'playcount': count
            }
            for album, count in album_counts.most_common(10)
        ]
        
        return {
            'total_plays': total_plays,
            'unique_tracks': unique_tracks,
            'unique_artists': unique_artists,
            'diversity_score': round(diversity_score, 3),
            'top_tracks': top_tracks,
            'top_artists': top_artists,
            'top_albums': top_albums
        }
    
    def get_last_update_time(self) -> datetime:
        """Get the timestamp of the last update"""
        if os.path.exists(self.last_update_file):
            try:
                with open(self.last_update_file, 'r') as f:
                    timestamp_str = f.read().strip()
                    return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        # If no update file, use the most recent scrobble timestamp
        if self.scrobbles:
            for scrobble in self.scrobbles:
                if scrobble.get('timestamp'):
                    try:
                        return self.parse_timestamp(scrobble['timestamp'])
                    except:
                        continue
        
        # Default to 7 days ago if no data
        return datetime.now() - timedelta(days=7)
    
    def fetch_new_scrobbles(self, from_timestamp: datetime) -> List[Dict[str, Any]]:
        """Fetch new scrobbles from Last.fm API since the given timestamp"""
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
                                scrobble_time = self.parse_timestamp(scrobble['timestamp'])
                                if scrobble_time > from_timestamp:
                                    new_scrobbles.append(scrobble)
                                else:
                                    print("✅ Reached cutoff time, stopping fetch")
                                    return new_scrobbles
                            except:
                                continue
                
                # Check if there are more pages
                if 'recenttracks' in data and '@attr' in data['recenttracks']:
                    total_pages = int(data['recenttracks']['@attr'].get('totalPages', 1))
                
                page += 1
                
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
                break
        
        print(f"✅ Fetched {len(new_scrobbles)} new scrobbles")
        return new_scrobbles
    
    def update_scrobbles(self) -> bool:
        """Update scrobbles database with new data from Last.fm API"""
        try:
            print("🔄 Checking for new scrobbles...")
            last_update = self.get_last_update_time()
            new_scrobbles = self.fetch_new_scrobbles(last_update)
            
            if not new_scrobbles:
                print("📭 No new scrobbles found")
                return True
            
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
                
                # Save updated data
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(all_scrobbles, f, indent=2, ensure_ascii=False)
                
                # Update the last update timestamp
                with open(self.last_update_file, 'w') as f:
                    f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                
                # Reload scrobbles
                self.scrobbles = all_scrobbles
                
                print(f"📈 Added {len(truly_new)} new scrobbles to database")
                print(f"📊 Total scrobbles now: {len(self.scrobbles):,}")
                return True
            else:
                print("📭 No new unique scrobbles to add")
                return True
                
        except Exception as e:
            print(f"❌ Error updating scrobbles: {e}")
            return False

# Global instance
advanced_analytics = AdvancedAnalytics()
