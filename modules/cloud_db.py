import os
from supabase import create_client, Client

# --- CONFIGURATION (Paste from Supabase Settings -> API) ---
SUPABASE_URL = "https://lryuqzddbhxbsdyzyxjb.supabase.co"
SUPABASE_KEY = "sb_publishable_6U4tpUtaF4Nn7_mGfKP9ig_WAk_av4Q"

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

def save_to_cloud(date_str, summary, local_audio_path, local_image_path, user_id="ryo"):
    """Saves text to DB and media to Storage."""
    print(f"☁️ Syncing {date_str} for user '{user_id}'...")

    # 1. Upload Audio
    audio_cloud_path = f"audio/{date_str}.wav"
    audio_url = upload_file(local_audio_path, audio_cloud_path)
    
    # 2. Upload Image (if exists)
    image_url = None
    if local_image_path:
        ext = os.path.splitext(local_image_path)[1] # get .jpg or .heic
        image_cloud_path = f"images/{date_str}{ext}"
        image_url = upload_file(local_image_path, image_cloud_path)

    # 3. Save Data (Upsert)
    data = {
        "user_id": user_id,
        "date": date_str,
        "summary": summary,
        "audio_url": audio_url,
        "image_url": image_url
    }
    
    try:
        # .upsert() updates the row if 'date' exists, or inserts if new
        supabase.table("entries").upsert(data).execute()
        print("✅ Cloud Save Complete!")
    except Exception as e:
        print(f"❌ Database Error: {e}")

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