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

def save_entry(date_str, summary, audio_bytes, image_path, is_edited=False, is_public=False):
    """Saves entry locally with is_edited AND is_public flags."""
    
    # 1. Save Audio File
    local_audio_path = f"recordings/{date_str}.wav"
    if not os.path.exists("recordings"):
        os.makedirs("recordings")
        
    with open(local_audio_path, "wb") as f:
        f.write(audio_bytes)
    
    # 2. Update Local Database
    db = load_db()
    db[date_str] = {
        "summary": summary,
        "audio_path": local_audio_path,
        "image_path": image_path,
        "image_url": None,
        "is_edited": is_edited,
        "is_public": is_public  # <--- NOW SAVING THIS
    }
    
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

def update_local_text(date_str, new_text):
    """Updates the text summary in the local JSON file."""
    db = load_db() # Load current data
    
    if date_str in db:
        # Update the specific fields
        db[date_str]["summary"] = new_text
        db[date_str]["is_edited"] = True
        
        # Save back to disk (using the same logic as save_entry)
        with open(DB_FILE, "w") as f:
            json.dump(db, f, indent=4)

def update_local_privacy(date_str, is_public):
    """Updates just the privacy setting locally."""
    db = load_db()
    if date_str in db:
        db[date_str]["is_public"] = is_public
        with open(DB_FILE, "w") as f:
            json.dump(db, f, indent=4)