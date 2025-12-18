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

# Prefer Streamlit secrets, then fall back to environment
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")

supabase: Client | None = None
if not SUPABASE_URL or not SUPABASE_KEY:
    # This prevents the app from crashing silently if keys are missing
    print("⚠️ Error: Supabase keys are missing from .env or Secrets.")
else:
    try:
        # Initialize
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"❌ Supabase init error: {e}")
        supabase = None

def upload_file(file_data, destination_path, bucket_name="diary_assets"):
    """
    Uploads a file (path string OR raw bytes) to Supabase Storage.
    Returns the Public URL.
    """
    try:
        # Check if file_data is bytes (from memory) or string (file path)
        if isinstance(file_data, bytes):
            # Upload bytes directly
            supabase.storage.from_(bucket_name).upload(
                path=destination_path,
                file=file_data,
                file_options={"content-type": "audio/wav"} # Force correct type
            )
        else:
            # It's a file path (string), open and upload
            with open(file_data, 'rb') as f:
                supabase.storage.from_(bucket_name).upload(
                    path=destination_path,
                    file=f
                )
        
        # Get Public URL
        return supabase.storage.from_(bucket_name).get_public_url(destination_path)
        
    except Exception as e:
        print(f"Upload Error: {e}")
        return None


def save_to_cloud(date_str, summary, local_audio_path, local_image_path, user_id="ryo", is_public=False, is_edited=False):
    """Saves entry with privacy AND edit status."""
    print(f"☁️ Syncing {date_str} (Public: {is_public}, Edited: {is_edited})...")

    if supabase is None:
        print("❌ Supabase client not initialized; skipping cloud save.")
        return False

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
        if supabase is None:
            return {}
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
        if supabase is None:
            return False
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
        if supabase is None:
            return {}
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
        if supabase is None:
            return False
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
        if supabase is None:
            return False
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

# ... inside modules/cloud_db.py ...

# Configuration
DUMMY_DOMAIN = "diary.local" # The invisible email suffix

def sign_up(username, password):
    """
    Registers a new user using ONLY username and password.
    Behind the scenes, it creates 'username@diary.local'.
    """
    # 1. Create the 'fake' email
    email = f"{username}@{DUMMY_DOMAIN}"
    
    try:
        if supabase is None:
            return False
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "username": username.lower() # Store plain username in metadata
                }
            }
        })
        # If successful, response.user will exist
        if response.user:
            return True
        return False
    except Exception as e:
        print(f"Sign Up Error: {e}")
        return False

def login(username, password):
    """
    Logs in using ONLY username and password.
    """
    # 1. Reconstruct the 'fake' email
    email = f"{username}@{DUMMY_DOMAIN}"
    
    try:
        if supabase is None:
            return None
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        # 2. Return the clean username (from metadata)
        user_meta = response.user.user_metadata
        return user_meta.get("username")
    except Exception as e:
        # Don't print the error to user, just return None
        return None

def get_current_user():
    """
    Checks if there is a valid session locally (in the Supabase client).
    Returns the username if logged in, None otherwise.
    """
    if supabase is None:
        return None
    session = supabase.auth.get_session()
    if session:
        # If the token is valid, get the metadata (username)
        return session.user.user_metadata.get("username")
    return None



def get_pending_requests(username):
    """
    Returns list of people waiting for YOU to accept.
    """
    try:
        if supabase is None:
            return []
        res = supabase.table("friends").select("*").eq("receiver", username).eq("status", "pending").execute()
        return res.data
    except:
        return []


def get_my_friends(username):
    """
    Returns a simple list of usernames: ['syd', 'alex']
    Checks both 'Sender' and 'Receiver' columns for 'accepted' status.
    """
    try:
        if supabase is None:
            return []
        # Find rows where I am sender OR receiver, AND status is accepted
        res = supabase.table("friends").select("*").or_(f"sender.eq.{username},receiver.eq.{username}").eq("status", "accepted").execute()
        
        friends = []
        for row in res.data:
            # If I was the sender, the friend is the receiver (and vice versa)
            if row["sender"] == username:
                friends.append(row["receiver"])
            else:
                friends.append(row["sender"])
        return friends
    except:
        return []

def logout():
    """
    Destroys the Supabase session so auto-login doesn't trigger again.
    """
    try:
        if supabase is None:
            return
        supabase.auth.sign_out()
    except Exception as e:
        print(f"Logout Error: {e}")

# 1. NEW: Generic Notification Function
def add_notification(target_user, message):
    try:
        if supabase is None:
            return
        supabase.table("notifications").insert({
            "user_id": target_user,
            "message": message
        }).execute()
    except Exception as e:
        print(f"Notif Error: {e}")

# 2. NEW: Check & Clear Notifications
def check_notifications(username):
    """
    Reads unread notifications, returns them, and marks them as read.
    """
    try:
        if supabase is None:
            return []
        # Fetch unread
        res = supabase.table("notifications").select("*").eq("user_id", username).eq("is_read", False).execute()
        notifs = res.data
        
        if notifs:
            # Mark as read immediately so they don't show up twice
            notif_ids = [n['id'] for n in notifs]
            supabase.table("notifications").update({"is_read": True}).in_("id", notif_ids).execute()
            
        return [n['message'] for n in notifs]
    except:
        return []

# 3. UPDATE: Send Friend Request (Now sends notification!)
def send_friend_request(from_user, to_user):
    if from_user == to_user:
        return False, "You can't add yourself 😜"

    try:
        if supabase is None:
            return False, "Supabase not configured."
        # A. Create the Friend Request
        supabase.table("friends").insert({
            "sender": from_user,
            "receiver": to_user,
            "status": "pending"
        }).execute()
        
        # B. Notify the Receiver
        add_notification(to_user, f"👋 New friend request from {from_user}!")
        
        return True, "Request sent!"
    except Exception as e:
        return False, "Request already sent or user not found."

# 4. UPDATE: Accept Friend (Now sends notification!)
def accept_friend(request_id):
    try:
        # A. Look up the request row so we know who to notify
        select_res = (
            supabase
            .table("friends")
            .select("*")
            .eq("id", request_id)
            .execute()
        )

        if not select_res.data:
            return

        friend_row = select_res.data[0]
        sender_name = friend_row["sender"]
        receiver_name = friend_row["receiver"]

        # B. Update status to accepted
        supabase.table("friends").update({"status": "accepted"}).eq("id", request_id).execute()

        # C. Notify the sender
        add_notification(sender_name, f"✅ {receiver_name} accepted your friend request!")

    except Exception as e:
        print(f"Accept Error: {e}")