#!/usr/bin/env python3
"""
Example usage of the Last.fm API Client
"""

from lastfm_client import LastFMClient, TimeRange, create_time_ranges, format_stats_summary
from datetime import datetime, timedelta

def main():
    # Initialize the client with your API key
    # Get your API key from: https://www.last.fm/api/account/create
    API_KEY = "your_api_key_here"  # Replace with your actual API key
    USERNAME = "your_username"     # Replace with your Last.fm username
    
    # Create the client
    client = LastFMClient(api_key=API_KEY)
    
    print("=== Last.fm API Client Examples ===\n")
    
    # Example 1: Get recent tracks from the last week
    print("1. Recent tracks from last week:")
    try:
        last_week = TimeRange.from_days_ago(7)
        recent_tracks = client.get_user_recent_tracks(USERNAME, time_range=last_week, limit=10)
        
        for i, track in enumerate(recent_tracks[:5], 1):
            print(f"   {i}. {track.artist} - {track.name}")
            if track.timestamp:
                print(f"      Played: {track.timestamp.strftime('%Y-%m-%d %H:%M')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Get top artists for different time periods
    print("2. Top artists comparison:")
    try:
        # Last month
        last_month = TimeRange.from_days_ago(30)
        top_artists_month = client.get_user_top_artists(USERNAME, time_range=last_month, limit=5)
        
        print("   Last month:")
        for i, artist in enumerate(top_artists_month, 1):
            print(f"   {i}. {artist.name} ({artist.playcount:,} plays)")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Get comprehensive user statistics
    print("3. User statistics for last 3 months:")
    try:
        last_3_months = TimeRange.from_days_ago(90)
        stats = client.get_user_stats(USERNAME, time_range=last_3_months)
        
        print(format_stats_summary(stats))
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 4: Search for specific activity
    print("4. Search for specific artist/track:")
    try:
        search_query = "beatles"  # Search for Beatles
        search_results = client.search_user_activity(USERNAME, search_query, last_3_months)
        
        print(f"   Found {len(search_results)} tracks matching '{search_query}':")
        for track in search_results[:3]:
            print(f"   - {track.artist} - {track.name}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 5: Using predefined time ranges
    print("5. Using predefined time ranges:")
    try:
        time_ranges = create_time_ranges()
        
        # Get stats for this year
        this_year_stats = client.get_user_stats(USERNAME, time_ranges['this_year'])
        print(f"   This year: {this_year_stats.get('total_plays', 0):,} total plays")
        
        # Get stats for last year
        last_year_stats = client.get_user_stats(USERNAME, time_ranges['last_year_full'])
        print(f"   Last year: {last_year_stats.get('total_plays', 0):,} total plays")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 6: Custom time range
    print("6. Custom time range (last 2 weeks):")
    try:
        # Create custom time range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=14)
        custom_range = TimeRange(start_date, end_date)
        
        custom_tracks = client.get_user_recent_tracks(USERNAME, time_range=custom_range, limit=5)
        print(f"   Recent tracks from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}:")
        for track in custom_tracks:
            print(f"   - {track.artist} - {track.name}")
    except Exception as e:
        print(f"   Error: {e}")


def quick_start_example():
    """Minimal example to get started quickly"""
    print("=== Quick Start Example ===")
    
    # Step 1: Get your API key from https://www.last.fm/api/account/create
    # Step 2: Replace these with your actual values
    API_KEY = "your_api_key_here"
    USERNAME = "your_username"
    
    # Step 3: Create client and get data
    client = LastFMClient(api_key=API_KEY)
    
    try:
        # Get your top 10 tracks of all time
        top_tracks = client.get_user_top_tracks(USERNAME, limit=10)
        
        print(f"Top 10 tracks for {USERNAME}:")
        for i, track in enumerate(top_tracks, 1):
            print(f"{i}. {track.artist} - {track.name} ({track.playcount:,} plays)")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to:")
        print("1. Get a free API key from https://www.last.fm/api/account/create")
        print("2. Replace 'your_api_key_here' with your actual API key")
        print("3. Replace 'your_username' with your Last.fm username")


if __name__ == "__main__":
    # Run the quick start example first
    quick_start_example()
    
    print("\n" + "="*60 + "\n")
    
    # Uncomment the line below to run the full examples
    # main()
