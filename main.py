import streamlit as st
import datetime
import os
from modules import database, ai, mac_photos, image_loader, cloud_db

# ==========================================
# 1. INITIALIZATION (Crash Prevention)
# ==========================================
# We auto-assign the user to 'ryo' so no login is needed
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = "ryo"

if "step" not in st.session_state:
    st.session_state.step = 1

if "selected_photo" not in st.session_state:
    st.session_state.selected_photo = None

# ==========================================
# 2. MAIN APP SETUP
# ==========================================
current_user = st.session_state.logged_in_user

st.title("Chit Chat! 😋")

# --- SIDEBAR: SEARCH ---
st.sidebar.header("🔍 Search Memories")
search_term = st.sidebar.text_input("Find keyword")

# --- SIDEBAR: FRIEND VIEW ---
# Toggle between "My Diary" (Ryo) and "Friend's Diary"
view_mode = st.sidebar.radio("Mode", ["My Diary", "Friend's Diary"])

if view_mode == "Friend's Diary":
    friend_name = st.sidebar.text_input("Enter Friend's Username:")
    if friend_name:
        st.info(f"Viewing {friend_name}'s Diary")
        # Load Friend's Data from Cloud (Read-Only)
        db = cloud_db.fetch_entries_by_user(friend_name, viewer_is_owner=False)
        is_read_only = True
        active_user_view = friend_name
    else:
        st.warning("Enter a name above.")
        # If no name, load empty dict to prevent crash
        db = {}
        is_read_only = True
        active_user_view = "Unknown"
else:
    # Load My Data from Local Disk (Writable)
    db = database.load_db()
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
# 3. VIEW MODE
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

    # 2. SUMMARY (View & Finalize Logic)
    st.subheader("📝 Summary")
    
    is_edited = entry.get("is_edited", False)
    edit_mode_key = f"edit_mode_{date_str}"
    
    if edit_mode_key not in st.session_state:
        st.session_state[edit_mode_key] = False

    # --- LOGIC START ---

    if is_read_only:
        # Friend View
        st.markdown(entry["summary"])
        if is_edited:
            st.caption("*(This entry has been edited)*")

    elif is_edited:
        # CASE 1: ALREADY FINALIZED (The Lock 🔒)
        st.markdown(entry["summary"])
        st.caption("🔒 *Edited & Finalized*")
        # Note: We deliberately do NOT show the "Edit" button here.

    elif st.session_state[edit_mode_key]:
        # CASE 2: CURRENTLY EDITING
        new_summary = st.text_area("Update summary:", value=entry["summary"], height=150)
        col1, col2 = st.columns([1, 5])
        
        if col1.button("💾 Finalize"):
            # Update Cloud
            cloud_db.update_summary(date_str, current_user, new_summary)
            # Update Local
            with st.spinner("Finalizing entry..."):
                # 1. Update Cloud
                cloud_db.update_summary(date_str, current_user, new_summary)
                
                # 2. Update Local (only if on my Mac)
                if current_user == "ryo": 
                    database.update_local_text(date_str, new_summary)
            
            st.session_state[edit_mode_key] = False
            st.success("Finalized!")
            st.rerun()
            
        if col2.button("Cancel"):
            st.session_state[edit_mode_key] = False
            st.rerun()

    else:
        # CASE 3: CLEAN SLATE (Can still be edited once)
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

    # 4. PRIVACY SETTINGS (Always Editable)
    # Only show this control if it is MY diary
    if not is_read_only:
        st.markdown("---")
        st.subheader("🔒 Privacy")
        
        # Get current state (Default to False if missing)
        current_privacy = entry.get("is_public", False)
        
        # The Toggle
        new_privacy = st.toggle(
            "🌍 Make Public (Friends can see)", 
            value=current_privacy,
            key=f"privacy_toggle_{date_str}"
        )
        
        # Logic: If the toggle changed, save immediately
        if new_privacy != current_privacy:
            # 1. Update Cloud
            cloud_db.update_privacy(date_str, current_user, new_privacy)
            
            # 2. Update Local
            database.update_local_privacy(date_str, new_privacy)
            
            # 3. Refresh to lock in the new state
            st.toast(f"Privacy updated: {'Public' if new_privacy else 'Private'}")
            # We manually update the cache so we don't need a full reload
            entry["is_public"] = new_privacy
            db[date_str]["is_public"] = new_privacy

# ==========================================
# 4. RECORD MODE (The Linear 4-Step Flow)
# ==========================================
else:
    if is_read_only:
        st.info(f"🚫 {active_user_view} hasn't posted on this day.")
        st.stop()

    # --- STEP 1: PHOTO ---
    if st.session_state.step == 1:
        st.info("Step 1: Choose a photo")
        suggested_photos = mac_photos.get_photos_from_mac_library(selected_date)
        
        if suggested_photos:
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
        else:
            st.warning("No photos found.")
        
        st.markdown("---")
        if st.button("Skip / No Photo"):
            st.session_state.selected_photo = None
            st.session_state.step = 2
            st.rerun()

    # --- STEP 2: RECORD ---
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
            
            # Reset flags for next step
            st.session_state.is_edited_flag = False 
            st.session_state.is_editing_mode = False
            st.session_state.step = 3
            st.rerun()

    # --- STEP 3: REVIEW & EDIT ---
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

    # --- STEP 4: PRIVACY & SAVE ---
    elif st.session_state.step == 4:
        st.info("Step 4: Finalize & Upload")
        st.subheader("🔒 Privacy Settings")
        
        is_public = st.toggle("🌍 Make Public (Friends can see)", value=False)
        st.markdown("---")
        
        if st.button("🚀 Upload & Save"):
            with st.spinner("Saving to Diary..."): # Added spinner here too!
                try:
                    # 1. Local Save (Updated to pass is_public)
                    database.save_entry(
                        date_str, 
                        st.session_state.temp_summary, 
                        st.session_state.temp_audio, 
                        st.session_state.selected_photo, 
                        is_edited=st.session_state.is_edited_flag,
                        is_public=is_public  # <--- PASS THE TOGGLE VALUE
                    )

                    # 2. Cloud Save
                    cloud_db.save_to_cloud(
                        date_str, 
                        st.session_state.temp_summary, 
                        f"recordings/{date_str}.wav", 
                        st.session_state.selected_photo,
                        user_id=st.session_state.logged_in_user,
                        is_public=is_public,
                        is_edited=st.session_state.is_edited_flag
                    )
                    
                    st.toast("✅ Saved Successfully!")
                    # Cleanup
                    del st.session_state.temp_summary
                    del st.session_state.temp_audio
                    st.session_state.step = 1
                    st.rerun()

                except Exception as e:
                    st.error(f"Error saving: {e}")