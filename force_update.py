#!/usr/bin/env python3
"""
Force database update to get latest scrobbles
"""

from smart_db import smart_db
from datetime import datetime

print("🔄 Forcing database update...")
print(f"Current database has {len(smart_db.scrobbles)} scrobbles")

# Clear the last update timestamp to force a full update
import os
if os.path.exists(smart_db.last_update_file):
    os.remove(smart_db.last_update_file)
    print("🗑️  Cleared last update timestamp")

# Force update
print("\n🔄 Running update...")
result = smart_db.update_database()
print(f"Update result: {result}")

print(f"\n📊 After update:")
print(f"Database has {len(smart_db.scrobbles)} scrobbles")
if smart_db.scrobbles:
    print(f"Most recent scrobble: {smart_db.scrobbles[0].get('timestamp', 'No timestamp')}")
    print(f"Sample recent scrobbles:")
    for i, scrobble in enumerate(smart_db.scrobbles[:5]):
        print(f"  {i+1}. {scrobble.get('artist', 'Unknown')} - {scrobble.get('name', 'Unknown')} ({scrobble.get('timestamp', 'No timestamp')})")
