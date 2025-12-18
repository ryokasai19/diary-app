import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# 2. Robust Key Fetcher
# Tries Streamlit Secrets first (Cloud), then Environment Variables (Local)
def get_secret(key):
    if key in st.secrets:
        return st.secrets[key]
    return os.getenv(key)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # This prevents the app from crashing silently if keys are missing
    print("⚠️ Error: Supabase keys are missing from .env or Secrets.")

# Initialize
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_file(local_path, destination_path):
    """Uploads file to Supabase Storage and returns public URL."""
    if not local_path or not os.path.exists(local_path):
        return None
    
    try:
        bucket = "diary_uploads"
        
        with open(local_path, 'rb') as f:
            # Upsert=True means "overwrite if it already exists"
            supabase.storage.from_(bucket).upload(
                file=f,
                path=destination_path,
                file_options={"content-type": "application/octet-stream", "upsert": "true"}
            )
        
        # Get the clean Public URL
        public_url = supabase.storage.from_(bucket).get_public_url(destination_path)
        return public_url
        
    except Exception as e:
        print(f"⚠️ Cloud Upload Error: {e}")
        return None


def save_to_cloud(date_str, summary, local_audio_path, local_image_path, user_id="ryo", is_public=False, is_edited=False):
    """Saves entry with privacy AND edit status."""
    print(f"☁️ Syncing {date_str} (Public: {is_public}, Edited: {is_edited})...")

    # 1. Upload Audio (Pass BOTH the file path AND the cloud destination)
    audio_url = upload_file(local_audio_path, f"audio/{user_id}/{date_str}.wav")
    
    # 2. Upload Image
    image_url = None
    if local_image_path:
        # Get extension (like .jpg) safely
        ext = os.path.splitext(local_image_path)[1]
        # Pass BOTH the file path AND the cloud destination
        image_url = upload_file(local_image_path, f"images/{user_id}/{date_str}{ext}")

    data = {
        "user_id": user_id,
        "date": date_str,
        "summary": summary,
        "audio_url": audio_url,
        "image_url": image_url,
        "is_public": is_public,
        "is_edited": is_edited  # <--- NEW FIELD
    }
    
    try:
        supabase.table("entries").upsert(data).execute()
        return True
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return False

# --- NEW FUNCTION: Fetch Friend's Data ---
def fetch_entries_by_user(target_user_id):
    """Downloads all diary entries for a specific friend."""
    try:
        response = supabase.table("entries").select("*").eq("user_id", target_user_id).execute()
        
        # Convert list of rows into our dictionary format: { "2025-12-17": { ... } }
        cloud_data = {}
        for row in response.data:
            date_key = row["date"]
            cloud_data[date_key] = {
                "summary": row["summary"],
                "audio_path": None,      # Cloud audio isn't local
                "audio_url": row["audio_url"], # But we have the URL!
                "image_path": None,
                "image_url": row["image_url"]
            }
        return cloud_data
        
    except Exception as e:
        print(f"❌ Fetch Error: {e}")
        return {}


def update_summary(date_str, user_id, new_summary):
    """Updates only the text summary of an entry."""
    try:
        supabase.table("entries").update({
            "summary": new_summary,
            "is_edited": True
        }).eq("user_id", user_id).eq("date", date_str).execute()
        return True
    except Exception as e:
        print(f"❌ Update Error: {e}")
        return False

def fetch_entries_by_user(target_user_id, viewer_is_owner=False):
    """
    Downloads entries. 
    If viewer_is_owner is False, ONLY fetches public entries.
    """
    try:
        query = supabase.table("entries").select("*").eq("user_id", target_user_id)
        
        # KEY LOGIC: If I'm not the owner, force the 'is_public' filter
        if not viewer_is_owner:
            query = query.eq("is_public", True)
            
        response = query.execute()
        
        # Convert to dictionary format
        cloud_data = {}
        for row in response.data:
            date_key = row["date"]
            cloud_data[date_key] = {
                "summary": row["summary"],
                "audio_path": None,
                "audio_url": row["audio_url"],
                "image_path": None, # Cloud entries don't have local paths
                "image_url": row["image_url"],
                "is_public": row.get("is_public", False),
                "is_edited": row.get("is_edited", False)
            }
        return cloud_data
        
    except Exception as e:
        print(f"❌ Fetch Error: {e}")
        return {}

def update_privacy(date_str, user_id, is_public):
    """Updates just the privacy setting."""
    try:
        supabase.table("entries").update({
            "is_public": is_public
        }).eq("user_id", user_id).eq("date", date_str).execute()
        return True
    except Exception as e:
        print(f"❌ Privacy Update Error: {e}")
        return False


def check_login(username, password):
    """Verifies username and password against Supabase."""
    try:
        # Query the 'app_users' table we just created
        response = supabase.table("app_users").select("*")\
            .eq("username", username)\
            .eq("password", password)\
            .execute()
        
        # If we get data back, the user exists!
        return len(response.data) > 0
    except Exception as e:
        print(f"Login Check Error: {e}")
        return False