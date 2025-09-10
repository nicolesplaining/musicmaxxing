#!/usr/bin/env python3
"""
Fix database sorting to ensure newest scrobbles are first
"""

from smart_db import smart_db
from datetime import datetime

print("🔧 Fixing database sorting...")
print(f"📊 Database has {len(smart_db.scrobbles)} scrobbles")

# Sort the database by timestamp (newest first)
def sort_key(scrobble):
    timestamp = scrobble.get('timestamp', '')
    if not timestamp:
        return ''
    try:
        # Parse timestamp (format: "01 Apr 2023, 03:59")
        return datetime.strptime(timestamp, "%d %b %Y, %H:%M")
    except ValueError:
        return datetime.min

print("🔄 Sorting database by timestamp...")
smart_db.scrobbles.sort(key=sort_key, reverse=True)

print("💾 Saving sorted database...")
smart_db.save_scrobbles(smart_db.scrobbles)

print("✅ Database sorted successfully!")
print("📊 First 5 scrobbles after sorting:")
for i, scrobble in enumerate(smart_db.scrobbles[:5]):
    print(f"  {i+1}. {scrobble['artist']} - {scrobble['name']} ({scrobble['timestamp']})")
