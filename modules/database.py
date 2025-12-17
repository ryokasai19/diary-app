import json
import os
import shutil

DB_FILE = "diary_db.json"
AUDIO_DIR = "recordings"
IMAGE_DIR = "image_path"

# Ensure audio directory exists when this module is imported
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)
if not os.path.exists(IMAGE_DIR):   
    os.makedirs(IMAGE_DIR)

def load_db():
    """Loads the database (JSON) into a Python Dictionary."""
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_entry(date_str, summary_text, audio_bytes, image_source_path=None):
    """Saves a new entry to the JSON HashMap and the Audio file."""
    # 1. Save Audio
    filename = f"{AUDIO_DIR}/{date_str}.wav"
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    

    # 2. Save Image
    saved_image_path = None
    if image_source_path:
        # Get the file extension (e.g., .heic or .jpg)
        ext = os.path.splitext(image_source_path)[1]
        image_filename = f"{date_str}{ext}"
        saved_image_path = os.path.join(IMAGE_DIR, image_filename)
        
        # Copy the file from Mac Photos to our app folder
        shutil.copy2(image_source_path, saved_image_path)

    # 3. Update DB
    db = load_db()
    db[date_str] = {
        "summary": summary_text,
        "audio_path": filename,
        "image_path": saved_image_path
    }
    
    # 4. Save JSON
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)