import streamlit as st
import datetime
import os
from modules import ai, mac_photos, image_loader, cloud_db
from PIL import Image, ExifTags


# ==========================================
# 1. INITIALIZATION
# ==========================================
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if "step" not in st.session_state:
    st.session_state.step = 1

if "selected_photo" not in st.session_state:
    st.session_state.selected_photo = None

# ==========================================
# 2. LOGIN GATE
# ==========================================
if not st.session_state.logged_in_user:
    st.title("🔒 Diary Login")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        username_input = st.text_input("Username").lower()
        password_input = st.text_input("Password", type="password")
    
    if st.button("Log In"):
        if cloud_db.check_login(username_input, password_input):
            st.session_state.logged_in_user = username_input
            st.success("Login Successful!")
            st.rerun()
        else:
            st.error("Incorrect username or password.")
    st.stop()

# ==========================================
# 3. MAIN APP SETUP
# ==========================================
current_user = st.session_state.logged_in_user

# Sidebar: Logout
st.sidebar.title(f"👋 Hi, {current_user.title()}")
if st.sidebar.button("Log Out"):
    st.session_state.logged_in_user = None
    st.rerun()

st.title("Chit Chat! 😋")

# --- SIDEBAR: SEARCH ---
st.sidebar.header("🔍 Search Memories")
search_term = st.sidebar.text_input("Find keyword")

# --- SIDEBAR: VIEW MODE ---
view_mode = st.sidebar.radio("Mode", ["My Diary", "Friend's Diary"])

if view_mode == "Friend's Diary":
    friend_name = st.sidebar.text_input("Enter Friend's Username:")
    if friend_name:
        db = cloud_db.fetch_entries_by_user(friend_name, viewer_is_owner=False)
        is_read_only = True
        active_user_view = friend_name
    else:
        db = {}
        is_read_only = True
        active_user_view = "Unknown"
else:
    # "My Diary" - ALWAYS LOAD FROM CLOUD
    db = cloud_db.fetch_entries_by_user(current_user, viewer_is_owner=True)
    is_read_only = False
    active_user_view = current_user

# --- CALENDAR SETUP ---
def go_to_date(new_date):
    st.session_state.date_picker = new_date

if search_term:
    results = [d for d, data in db.items() if search_term.lower() in data["summary"].lower()]
    st.sidebar.markdown(f"**Found {len(results)} entries:**")
    for date_result in results:
        y, m, d = map(int, date_result.split("-"))
        st.sidebar.button(f"📅 {date_result}", key=f"btn_{date_result}", on_click=go_to_date, args=(datetime.date(y, m, d),))

if "date_picker" not in st.session_state:
    st.session_state.date_picker = datetime.date.today()

selected_date = st.date_input("Select a date", key="date_picker")
date_str = str(selected_date)

# Reset state when date changes
if "last_date" not in st.session_state or st.session_state.last_date != date_str:
    st.session_state.last_date = date_str
    st.session_state.step = 1
    st.session_state.selected_photo = None

# ==========================================
# 4. VIEW MODE
# ==========================================
if date_str in db:
    entry = db[date_str]
    
    # 1. PHOTO
    local_path = entry.get("image_path")
    cloud_url = entry.get("image_url")
    
    st.caption(f"📅 Memory from {date_str}")

    if local_path and os.path.exists(local_path):
        img_data = image_loader.load_image_for_streamlit(local_path)
        if img_data: st.image(img_data)
    elif cloud_url:
        st.info("☁️ Loading image from Cloud...")
        st.image(cloud_url)
    elif local_path:
        st.warning("⚠️ Photo missing from disk.")

    # 2. SUMMARY
    st.subheader("📝 Summary")
    
    is_edited = entry.get("is_edited", False)
    edit_mode_key = f"edit_mode_{date_str}"
    if edit_mode_key not in st.session_state:
        st.session_state[edit_mode_key] = False

    if is_read_only:
        st.markdown(entry["summary"])
        if is_edited: st.caption("*(This entry has been edited)*")

    elif is_edited:
        st.markdown(entry["summary"])
        st.caption("🔒 *Edited & Finalized*")

    elif st.session_state[edit_mode_key]:
        new_summary = st.text_area("Update summary:", value=entry["summary"], height=150)
        col1, col2 = st.columns([1, 5])
        
        if col1.button("💾 Finalize"):
            with st.spinner("Finalizing..."):
                cloud_db.update_summary(date_str, current_user, new_summary)
            st.session_state[edit_mode_key] = False
            st.success("Finalized!")
            st.rerun()
            
        if col2.button("Cancel"):
            st.session_state[edit_mode_key] = False
            st.rerun()
    else:
        st.markdown(entry["summary"])
        if st.button("✏️ Edit Text"):
            st.session_state[edit_mode_key] = True
            st.rerun()
    
    # 3. AUDIO
    st.subheader("🎧 Recording")
    audio_path = entry.get("audio_path")
    audio_url = entry.get("audio_url")
    
    if audio_path and os.path.exists(audio_path):
        st.audio(audio_path)
    elif audio_url:
        st.audio(audio_url)
    else:
        st.info("No audio available.")

    # 4. PRIVACY
    if not is_read_only:
        st.markdown("---")
        st.subheader("🔒 Privacy")
        current_privacy = entry.get("is_public", False)
        new_privacy = st.toggle("🌍 Make Public (Friends can see)", value=current_privacy, key=f"privacy_toggle_{date_str}")
        
        if new_privacy != current_privacy:
            cloud_db.update_privacy(date_str, current_user, new_privacy)
            st.toast(f"Privacy updated: {'Public' if new_privacy else 'Private'}")
            entry["is_public"] = new_privacy

# ==========================================
# 5. RECORD MODE
# ==========================================
else:
    if is_read_only:
        st.info(f"🚫 {active_user_view} hasn't posted on this day.")
        st.stop()

    # STEP 1: PHOTO
    if st.session_state.step == 1:
        st.info("Step 1: Choose a photo")
        
        # A. Try Mac Photos
        suggested_photos = mac_photos.get_photos_from_mac_library(selected_date)
        if suggested_photos:
            st.write("📸 From your Mac Library:")
            cols = st.columns(3)
            for idx, photo_path in enumerate(suggested_photos):
                img_data = image_loader.load_image_for_streamlit(photo_path)
                if img_data:
                    with cols[idx % 3]:
                        st.image(img_data)
                        if st.button("Select", key=f"btn_{idx}", use_container_width=True):
                            st.session_state.selected_photo = photo_path
                            st.session_state.step = 2 
                            st.rerun()
            st.markdown("---")

        # B. Upload Button (Mobile Friendly)
        st.write("📂 Upload from Device (iPhone/Android/PC):")
        uploaded_file = st.file_uploader("Pick a photo...", type=['jpg', 'jpeg', 'png', 'heic'])
        
        if uploaded_file is not None:
            try:
                # 1. Open Image to check metadata
                img = Image.open(uploaded_file)
                exif_data = img._getexif()
                photo_date = None

                if exif_data:
                    # Look for DateTimeOriginal (Tag 36867)
                    for tag, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag, tag)
                        if tag_name == "DateTimeOriginal":
                            # Format is usually "YYYY:MM:DD HH:MM:SS"
                            date_part = value.split(" ")[0].replace(":", "-")
                            photo_date = date_part
                            break
                
                # 2. Validate Date
                target_date_str = str(selected_date)
                
                if photo_date and photo_date != target_date_str:
                    st.error(f"⚠️ Date Mismatch! This photo was taken on {photo_date}, but you are writing for {target_date_str}.")
                    # Don't save it.
                else:
                    if not photo_date:
                        st.warning("⚠️ No date found in photo metadata. Accepting anyway (be careful!).")
                    
                    # 3. Save Temp File (Only if valid)
                    temp_filename = f"temp_upload_{selected_date}.jpg"
                    with open(temp_filename, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    st.session_state.selected_photo = temp_filename
                    st.session_state.step = 2
                    st.rerun()

            except Exception as e:
                st.error(f"Error processing image: {e}")

        st.markdown("---")
        if st.button("Skip / No Photo"):
            st.session_state.selected_photo = None
            st.session_state.step = 2
            st.rerun()

    # STEP 2: RECORD
    elif st.session_state.step == 2:
        st.info("Step 2: Record your thoughts")
        if st.session_state.selected_photo:
            preview = image_loader.load_image_for_streamlit(st.session_state.selected_photo)
            if preview: st.image(preview, width=150)

        audio_value = st.audio_input(f"Record for {date_str}")
        if audio_value:
            st.spinner("Generating AI Summary...")
            st.session_state.temp_audio = audio_value.read()
            st.session_state.temp_summary = ai.summarize_audio(st.session_state.temp_audio)
            
            st.session_state.is_edited_flag = False 
            st.session_state.is_editing_mode = False
            st.session_state.step = 3
            st.rerun()

    # STEP 3: REVIEW
    elif st.session_state.step == 3:
        st.info("Step 3: Review Draft")
        
        if st.session_state.is_editing_mode:
            st.subheader("✏️ Editing Draft")
            new_text = st.text_area("Make your changes:", value=st.session_state.temp_summary, height=200)
            if st.button("💾 Finalize Changes"):
                st.session_state.temp_summary = new_text
                st.session_state.is_edited_flag = True
                st.session_state.step = 4
                st.rerun()
        else:
            st.subheader("📝 AI Summary")
            st.markdown(st.session_state.temp_summary)
            st.markdown("---")
            col1, col2 = st.columns(2)
            if col1.button("✏️ Edit Text"):
                st.session_state.is_editing_mode = True
                st.rerun()
            if col2.button("✅ Looks Good (Next)"):
                st.session_state.step = 4
                st.rerun()

    # STEP 4: SAVE
    elif st.session_state.step == 4:
        st.info("Step 4: Finalize & Upload")
        st.subheader("🔒 Privacy Settings")
        is_public = st.toggle("🌍 Make Public (Friends can see)", value=False)
        st.markdown("---")
        
        if st.button("🚀 Upload & Save"):
            with st.spinner("Saving to Cloud..."):
                try:
                    cloud_db.save_to_cloud(
                        date_str, 
                        st.session_state.temp_summary, 
                        f"recordings/{date_str}.wav", 
                        st.session_state.selected_photo,
                        user_id=current_user,
                        is_public=is_public,
                        is_edited=st.session_state.is_edited_flag
                    )
                    st.toast("✅ Saved Successfully!")
                    del st.session_state.temp_summary
                    del st.session_state.temp_audio
                    st.session_state.step = 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving: {e}")