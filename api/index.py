#!/usr/bin/env python3
"""
Last.fm Music Analytics Web App - Vercel Deployment
A simplified Flask web application for Vercel deployment
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import json
import requests
from datetime import datetime, timedelta
from collections import Counter

app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates'),
           static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static'))
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Hardcoded user and API key
TARGET_USER = "nnicolema"
API_KEY = "b50c3e94c0f308ce124052b2e9ecfe3e"

def fetch_lastfm_data(method, params=None):
    """Fetch data from Last.fm API"""
    if params is None:
        params = {}
    
    params.update({
        'api_key': API_KEY,
        'format': 'json'
    })
    
    url = 'http://ws.audioscrobbler.com/2.0/'
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error fetching from Last.fm: {e}")
        return None

def get_user_recent_tracks(username, limit=50):
    """Get recent tracks from Last.fm API"""
    data = fetch_lastfm_data('user.getrecenttracks', {
        'method': 'user.getrecenttracks',
        'user': username,
        'limit': limit
    })
    
    if not data or 'recenttracks' not in data:
        return []
    
    tracks = data['recenttracks'].get('track', [])
    if not isinstance(tracks, list):
        tracks = [tracks]
    
    result = []
    for track in tracks:
        result.append({
            'name': track.get('name', ''),
            'artist': track.get('artist', {}).get('#text', '') if isinstance(track.get('artist'), dict) else track.get('artist', ''),
            'album': track.get('album', {}).get('#text', '') if isinstance(track.get('album'), dict) else track.get('album', ''),
            'timestamp': track.get('date', {}).get('#text', '') if isinstance(track.get('date'), dict) else 'Now playing',
            'loved': track.get('loved', '0') == '1'
        })
    
    return result

def get_user_top_tracks(username, period='7day', limit=10):
    """Get top tracks from Last.fm API"""
    data = fetch_lastfm_data('user.gettoptracks', {
        'method': 'user.gettoptracks',
        'user': username,
        'period': period,
        'limit': limit
    })
    
    if not data or 'toptracks' not in data:
        return []
    
    tracks = data['toptracks'].get('track', [])
    if not isinstance(tracks, list):
        tracks = [tracks]
    
    result = []
    for track in tracks:
        result.append({
            'name': track.get('name', ''),
            'artist': track.get('artist', {}).get('name', '') if isinstance(track.get('artist'), dict) else track.get('artist', ''),
            'playcount': int(track.get('playcount', 0))
        })
    
    return result

def get_user_top_artists(username, period='7day', limit=10):
    """Get top artists from Last.fm API"""
    data = fetch_lastfm_data('user.gettopartists', {
        'method': 'user.gettopartists', 
        'user': username,
        'period': period,
        'limit': limit
    })
    
    if not data or 'topartists' not in data:
        return []
    
    artists = data['topartists'].get('artist', [])
    if not isinstance(artists, list):
        artists = [artists]
    
    result = []
    for artist in artists:
        result.append({
            'name': artist.get('name', ''),
            'playcount': int(artist.get('playcount', 0))
        })
    
    return result

@app.route('/')
def index():
    """Home page - redirect directly to nnicolema dashboard"""
    return redirect(url_for('dashboard', username=TARGET_USER))

@app.route('/dashboard/<username>')
def dashboard(username):
    """User dashboard page"""
    return render_template('dashboard.html', username=username)

@app.route('/search/<username>')
def search_page(username):
    """Search page for a user"""
    return render_template('search.html', username=username)

@app.route('/analytics')
def advanced_analytics_page():
    """Advanced analytics page"""
    return render_template('advanced_analytics.html')

@app.route('/api/user/<username>')
def get_user_data(username):
    """Get user data from Last.fm API"""
    try:
        if username != TARGET_USER:
            return jsonify({'error': f'This app is optimized for {TARGET_USER} only'}), 400
        
        # Get user info
        user_data = fetch_lastfm_data('user.getinfo', {
            'method': 'user.getinfo',
            'user': username
        })
        
        user_info = {
            'name': username,
            'playcount': 0,
            'registered': 'Unknown',
            'url': f'https://www.last.fm/user/{username}'
        }
        
        if user_data and 'user' in user_data:
            user_info.update({
                'playcount': int(user_data['user'].get('playcount', 0)),
                'registered': user_data['user'].get('registered', {}).get('#text', 'Unknown')
            })
        
        # Get stats for different periods
        periods = ['7day', '1month', '3month', '6month', '12month', 'overall']
        stats_data = {}
        
        for period in periods:
            period_name = {
                '7day': 'last_week',
                '1month': 'last_month', 
                '3month': 'last_3_months',
                '6month': 'last_6_months',
                '12month': 'last_year',
                'overall': 'this_year'
            }.get(period, period)
            
            top_tracks = get_user_top_tracks(username, period, 10)
            top_artists = get_user_top_artists(username, period, 10)
            
            stats_data[period_name] = {
                'total_plays': sum(t['playcount'] for t in top_tracks),
                'unique_tracks': len(top_tracks),
                'unique_artists': len(top_artists),
                'top_tracks': top_tracks,
                'top_artists': top_artists,
                'top_albums': []  # Not easily available from API
            }
        
        return jsonify({
            'username': username,
            'user_info': user_info,
            'stats': stats_data,
            'database_info': {
                'total_scrobbles': user_info['playcount'],
                'source': 'Last.fm API'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<username>/recent')
def get_recent_tracks(username):
    """Get recent tracks from Last.fm API"""
    try:
        if username != TARGET_USER:
            return jsonify({'error': f'This app is optimized for {TARGET_USER} only'}), 400
        
        limit = request.args.get('limit', 50, type=int)
        tracks = get_user_recent_tracks(username, limit)
        
        return jsonify({
            'username': username,
            'tracks': tracks
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<username>/search')
def search_user_activity(username):
    """Search user's activity - simplified for API-only version"""
    try:
        if username != TARGET_USER:
            return jsonify({'error': f'This app is optimized for {TARGET_USER} only'}), 400
        
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # For now, return empty results as we don't have full scrobble history
        return jsonify({
            'username': username,
            'query': query,
            'results': [],
            'count': 0,
            'message': 'Search functionality requires full scrobble database'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<username>/custom-range')
def get_custom_range_stats(username):
    """Get custom range stats - simplified for API-only version"""
    try:
        if username != TARGET_USER:
            return jsonify({'error': f'This app is optimized for {TARGET_USER} only'}), 400
        
        return jsonify({
            'error': 'Custom range functionality requires full scrobble database',
            'message': 'This feature is not available in the serverless version'
        }), 501
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Simplified analytics endpoints
@app.route('/api/analytics/yearly-breakdown')
def yearly_breakdown():
    """Simplified yearly breakdown"""
    return jsonify({'message': 'Advanced analytics require full database'})

@app.route('/api/analytics/monthly-breakdown')
def monthly_breakdown():
    """Simplified monthly breakdown"""
    return jsonify({'message': 'Advanced analytics require full database'})

@app.route('/api/analytics/listening-patterns')
def listening_patterns():
    """Simplified listening patterns"""
    return jsonify({'message': 'Advanced analytics require full database'})

# Health check
@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Last.fm Analytics API is running'})

# Vercel handler
app = app