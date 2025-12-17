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

def save_to_cloud(date_str, summary, local_audio_path, local_image_path):
    """Saves text to DB and media to Storage."""
    print(f"☁️ Syncing {date_str} to Supabase...")

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