import json
import os

DB_FILE = "diary_db.json"
AUDIO_DIR = "recordings"

# Ensure audio directory exists when this module is imported
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

def load_db():
    """Loads the database (JSON) into a Python Dictionary."""
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_entry(date_str, summary_text, audio_bytes):
    """Saves a new entry to the JSON HashMap and the Audio file."""
    # 1. Save Audio
    filename = f"{AUDIO_DIR}/{date_str}.wav"
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    
    # 2. Update DB
    db = load_db()
    db[date_str] = {
        "summary": summary_text,
        "audio_path": filename
    }
    
    # 3. Save JSON
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)