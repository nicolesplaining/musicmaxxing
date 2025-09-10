#!/usr/bin/env python3
"""
Test if database is actually being updated with latest scrobbles
"""

from smart_db import smart_db
import os

# Clear the last update timestamp to force a full update
if os.path.exists(smart_db.last_update_file):
    os.remove(smart_db.last_update_file)
    print("🗑️  Cleared last update timestamp")

# Reload the database to get fresh data
smart_db.scrobbles = smart_db.load_scrobbles()
print(f"📊 Database loaded with {len(smart_db.scrobbles)} scrobbles")

# Check the first few scrobbles
print("📊 First 5 scrobbles in database:")
for i, scrobble in enumerate(smart_db.scrobbles[:5]):
    print(f"  {i+1}. {scrobble['artist']} - {scrobble['name']} ({scrobble['timestamp']})")

# Force update
print("\n🔄 Forcing database update...")
result = smart_db.update_database()
print(f"Update result: {result}")

# Check the first few scrobbles after update
print("\n📊 First 5 scrobbles after update:")
for i, scrobble in enumerate(smart_db.scrobbles[:5]):
    print(f"  {i+1}. {scrobble['artist']} - {scrobble['name']} ({scrobble['timestamp']})")

# Check if the database was actually updated
print(f"\n📊 Database now has {len(smart_db.scrobbles)} scrobbles")
