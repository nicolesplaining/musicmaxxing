#!/usr/bin/env python3
"""
Last.fm Music Analytics Web App
A Flask web application for visualizing Last.fm listening data
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from lastfm_client import LastFMClient, TimeRange, create_time_ranges, format_stats_summary
from smart_db import smart_db
from advanced_analytics import advanced_analytics
from datetime import datetime, timedelta
import os
import json
import pickle

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Global client instance
client = None

# Cache directory
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Hardcoded user
TARGET_USER = "nnicolema"

# Simple database is already initialized in simple_db.py

def get_client():
    """Get or create Last.fm client instance"""
    # Hardcoded API key for nnicolema user
    api_key = "b50c3e94c0f308ce124052b2e9ecfe3e"
    return LastFMClient(api_key=api_key)

def get_cache_path(cache_key):
    """Get cache file path for a given key"""
    return os.path.join(CACHE_DIR, f"{cache_key}.pkl")

def load_from_cache(cache_key, max_age_hours=24):
    """Load data from cache if it exists and is not too old"""
    cache_path = get_cache_path(cache_key)
    if not os.path.exists(cache_path):
        return None
    
    # Check if cache is too old
    cache_time = os.path.getmtime(cache_path)
    age_hours = (datetime.now().timestamp() - cache_time) / 3600
    if age_hours > max_age_hours:
        return None
    
    try:
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    except:
        return None

def save_to_cache(cache_key, data):
    """Save data to cache"""
    cache_path = get_cache_path(cache_key)
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
    except:
        pass  # Ignore cache errors

def get_cached_user_data(username, time_range_name, max_age_hours=24):
    """Get cached user data for a specific time range"""
    if username != TARGET_USER:
        return None  # Only cache for nnicolema
    
    cache_key = f"{username}_{time_range_name}"
    return load_from_cache(cache_key, max_age_hours)

def save_cached_user_data(username, time_range_name, data):
    """Save user data to cache"""
    if username != TARGET_USER:
        return  # Only cache for nnicolema
    
    cache_key = f"{username}_{time_range_name}"
    save_to_cache(cache_key, data)

@app.route('/')
def index():
    """Home page - redirect directly to nnicolema dashboard"""
    return redirect(url_for('dashboard', username=TARGET_USER))

@app.route('/setup')
def setup():
    """Setup page for API key configuration"""
    return render_template('setup.html')

@app.route('/api/configure', methods=['POST'])
def configure_api():
    """Configure API key"""
    data = request.get_json()
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({'error': 'API key is required'}), 400
    
    try:
        # Test the API key by making a simple request
        test_client = LastFMClient(api_key=api_key)
        # Try to get chart data which is more reliable for validation
        test_client._make_request('chart.gettopartists', {'limit': '1'})
        
        # Store in session
        session['api_key'] = api_key
        return jsonify({'success': True})
    except Exception as e:
        # If chart method fails, try a different validation method
        try:
            # Try to get top tracks globally
            test_client._make_request('chart.gettoptracks', {'limit': '1'})
            session['api_key'] = api_key
            return jsonify({'success': True})
        except Exception as e2:
            return jsonify({'error': f'Invalid API key. Please check your Last.fm API key and try again. Make sure you have a valid API key from https://www.last.fm/api/account/create'}), 400

@app.route('/api/user/<username>')
def get_user_data(username):
    """Get user data for nnicolema from raw scrobbles data"""
    try:
        print("🎯 Using ADVANCED ANALYTICS for user data")
        # Only work with nnicolema user
        if username != TARGET_USER:
            return jsonify({'error': f'This app is optimized for {TARGET_USER} only'}), 400
        
        # Calculate date ranges for different time periods
        now = datetime.now()
        time_periods = {
            'last_week': (now - timedelta(days=7), now),
            'last_month': (now - timedelta(days=30), now),
            'last_3_months': (now - timedelta(days=90), now),
            'last_6_months': (now - timedelta(days=180), now),
            'last_year': (now - timedelta(days=365), now),
            'this_year': (datetime(now.year, 1, 1), datetime(now.year, 12, 31, 23, 59, 59))
        }
        
        stats_data = {}
        total_scrobbles = len(advanced_analytics.scrobbles)
        
        for period_name, (start_dt, end_dt) in time_periods.items():
            try:
                # Convert datetime objects to date strings
                start_date = start_dt.strftime("%Y-%m-%d")
                end_date = end_dt.strftime("%Y-%m-%d")
                
                # Get scrobbles for this period
                scrobbles = advanced_analytics.get_scrobbles_in_range(start_date, end_date)
                stats = advanced_analytics.calculate_period_stats(scrobbles)
                stats_data[period_name] = stats
                
            except Exception as e:
                print(f"Error getting stats for {period_name}: {e}")
                stats_data[period_name] = {'error': str(e)}
        
        return jsonify({
            'username': username,
            'user_info': {
                'name': username,
                'playcount': total_scrobbles,
                'registered': 'Unknown',
                'url': f'https://www.last.fm/user/{username}'
            },
            'stats': stats_data,
            'database_info': {
                'total_scrobbles': total_scrobbles,
                'data_source': 'raw_scrobbles',
                'last_updated': 'real-time'
            },
            'cached': False,
            'smart_db': False,
            'incremental_updates': False,
            'raw_scrobbles': True
        })
        
    except Exception as e:
        print(f"Error getting user data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<username>/recent')
def get_recent_tracks(username):
    """Get recent tracks for nnicolema from simple database"""
    try:
        # Only work with nnicolema user
        if username != TARGET_USER:
            return jsonify({'error': f'This app is optimized for {TARGET_USER} only'}), 400
        
        limit = request.args.get('limit', 50, type=int)
        recent_tracks = smart_db.get_recent_tracks(limit)
        
        return jsonify({
            'username': username,
            'tracks': recent_tracks,
            'simple_db': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<username>/search')
def search_user_activity(username):
    """Search user's listening activity"""
    try:
        # Only work with nnicolema user
        if username != TARGET_USER:
            return jsonify({'error': f'This app is optimized for {TARGET_USER} only'}), 400
        
        query = request.args.get('q', '')
        days = request.args.get('days', 30, type=int)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        results = smart_db.search_tracks(query, days)
        
        return jsonify({
            'username': username,
            'query': query,
            'results': results,
            'count': len(results),
            'simple_db': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<username>/custom-range')
def get_user_custom_range(username):
    """Get user data for a custom date range"""
    try:
        # Only work with nnicolema user
        if username != TARGET_USER:
            return jsonify({'error': f'This app is optimized for {TARGET_USER} only'}), 400
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date parameters required (YYYY-MM-DD format)'}), 400
        
        # Use the advanced analytics to get the data
        scrobbles = advanced_analytics.get_scrobbles_in_range(start_date, end_date)
        stats = advanced_analytics.calculate_period_stats(scrobbles)
        
        return jsonify({
            'username': username,
            'start_date': start_date,
            'end_date': end_date,
            'total_plays': stats['total_plays'],
            'unique_tracks': stats['unique_tracks'],
            'unique_artists': stats['unique_artists'],
            'diversity_score': stats['diversity_score'],
            'top_artists': stats['top_artists'],
            'top_tracks': stats['top_tracks'],
            'top_albums': stats['top_albums']
        })
        
    except Exception as e:
        print(f"Error getting custom range data: {e}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/test')
def test_page():
    """Test page for debugging fetch issues"""
    return app.send_static_file('test_fetch.html')

@app.route('/api/cache/clear')
def clear_cache():
    """Clear cache for nnicolema user"""
    try:
        import shutil
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
            os.makedirs(CACHE_DIR)
        return jsonify({'success': True, 'message': 'Cache cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/status')
def cache_status():
    """Get cache status for nnicolema user"""
    try:
        cache_files = []
        if os.path.exists(CACHE_DIR):
            for filename in os.listdir(CACHE_DIR):
                if filename.startswith(f"{TARGET_USER}_") and filename.endswith('.pkl'):
                    cache_path = os.path.join(CACHE_DIR, filename)
                    cache_time = os.path.getmtime(cache_path)
                    age_hours = (datetime.now().timestamp() - cache_time) / 3600
                    cache_files.append({
                        'file': filename,
                        'age_hours': round(age_hours, 2),
                        'size_kb': round(os.path.getsize(cache_path) / 1024, 2)
                    })
        
        return jsonify({
            'user': TARGET_USER,
            'cache_files': cache_files,
            'total_files': len(cache_files)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/status')
def database_status():
    """Get simple database status"""
    try:
        status = smart_db.get_database_info()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/initialize')
def initialize_database():
    """Database is already initialized with complete data"""
    try:
        info = smart_db.get_database_info()
        return jsonify({
            'success': True, 
            'message': 'Database already initialized with complete scrobble history',
            'info': info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== ADVANCED ANALYTICS ENDPOINTS =====

@app.route('/api/analytics/custom-range')
def custom_range_analytics():
    """Get analytics for a custom date range"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date parameters required (YYYY-MM-DD format)'}), 400
        
        scrobbles = advanced_analytics.get_scrobbles_in_range(start_date, end_date)
        stats = advanced_analytics.calculate_period_stats(scrobbles)
        
        return jsonify({
            'start_date': start_date,
            'end_date': end_date,
            'stats': stats,
            'total_scrobbles': len(scrobbles)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/yearly-breakdown')
def yearly_breakdown():
    """Get yearly listening breakdown"""
    try:
        yearly_stats = advanced_analytics.get_yearly_breakdown()
        return jsonify(yearly_stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/monthly-breakdown')
def monthly_breakdown():
    """Get monthly listening breakdown for a specific year"""
    try:
        year = request.args.get('year', type=int)
        if not year:
            year = datetime.now().year
        
        monthly_stats = advanced_analytics.get_monthly_breakdown(year)
        return jsonify({
            'year': year,
            'monthly_stats': monthly_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/listening-patterns')
def listening_patterns():
    """Get listening patterns by time of day and day of week"""
    try:
        patterns = advanced_analytics.get_listening_patterns()
        return jsonify(patterns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/artist-evolution')
def artist_evolution():
    """Track how an artist's popularity changes over time"""
    try:
        artist_name = request.args.get('artist')
        if not artist_name:
            return jsonify({'error': 'artist parameter required'}), 400
        
        evolution = advanced_analytics.get_artist_evolution(artist_name)
        return jsonify(evolution)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/compare-periods')
def compare_periods():
    """Compare two time periods"""
    try:
        period1_start = request.args.get('period1_start')
        period1_end = request.args.get('period1_end')
        period2_start = request.args.get('period2_start')
        period2_end = request.args.get('period2_end')
        
        if not all([period1_start, period1_end, period2_start, period2_end]):
            return jsonify({'error': 'All period parameters required (YYYY-MM-DD format)'}), 400
        
        comparison = advanced_analytics.get_comparative_analytics(
            period1_start, period1_end, period2_start, period2_end
        )
        return jsonify(comparison)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/seasonal')
def seasonal_analysis():
    """Get seasonal listening analysis"""
    try:
        seasonal_stats = advanced_analytics.get_seasonal_analysis()
        return jsonify(seasonal_stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/top-periods')
def top_periods():
    """Get top periods by any metric"""
    try:
        metric = request.args.get('metric', 'total_plays')
        period_type = request.args.get('period_type', 'month')
        
        top_periods = advanced_analytics.get_top_periods(metric, period_type)
        return jsonify({
            'metric': metric,
            'period_type': period_type,
            'top_periods': top_periods
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/shoegaze')
def shoegaze_analytics():
    """Get comprehensive shoegaze-specific analytics"""
    try:
        shoegaze_data = advanced_analytics.get_shoegaze_analytics()
        return jsonify(shoegaze_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
