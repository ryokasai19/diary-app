import json
import os
from modules import cloud_db

# Try to import DB_FILE, fallback if missing
try:
    from modules.database import DB_FILE
except ImportError:
    DB_FILE = "diary.json"

# 1. Load Local Data
if not os.path.exists(DB_FILE):
    print("❌ No local diary.json found.")
    exit()

with open(DB_FILE, "r") as f:
    local_data = json.load(f)

print(f"📦 Found {len(local_data)} entries to migrate...")

# 2. Loop and Upload
for date_str, entry in local_data.items():
    print(f"🚀 Uploading {date_str}...")
    
    # --- DEFINE VARIABLES (Check if files exist) ---
    
    # Check Audio
    audio_to_upload = entry.get("audio_path")
    if audio_to_upload and not os.path.exists(audio_to_upload):
        print(f"   ⚠️ Audio file missing: {audio_to_upload} (Skipping audio)")
        audio_to_upload = None  # Don't try to upload non-existent file

    # Check Image
    image_to_upload = entry.get("image_path")
    if image_to_upload and not os.path.exists(image_to_upload):
        print(f"   ⚠️ Image file missing: {image_to_upload} (Skipping image)")
        image_to_upload = None

    # --- UPLOAD ---
    try:
        cloud_db.save_to_cloud(
            date_str,                       # 1. Date
            entry["summary"],               # 2. Summary
            audio_to_upload,                # 3. Audio (File path or None)
            image_to_upload,                # 4. Image (File path or None)
            "ryo",                          # 5. User ID
            entry.get("is_public", False),  # 6. Public?
            entry.get("is_edited", False)   # 7. Edited?
        )
        print("   ✅ Done!")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

print("🎉 Migration Complete!")