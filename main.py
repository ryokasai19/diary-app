import streamlit as st
import datetime
import os
# Import your custom modules
from modules import database, ai, mac_photos, image_loader, cloud_db

st.title("Chit Chat! 😋")

# Load Data
db = database.load_db()

# --- SIDEBAR: SEARCH ---
st.sidebar.header("🔍 Search Memories")
search_term = st.sidebar.text_input("Find keyword")

def go_to_date(new_date):
    st.session_state.date_picker = new_date

if search_term:
    results = [d for d, data in db.items() if search_term.lower() in data["summary"].lower()]
    st.sidebar.markdown(f"**Found {len(results)} entries:**")
    for date_result in results:
        y, m, d = map(int, date_result.split("-"))
        st.sidebar.button(
            f"📅 {date_result}", 
            key=f"btn_search_{date_result}",
            on_click=go_to_date,
            args=(datetime.date(y, m, d),)
        )
    if not results:
        st.sidebar.caption("No matches found.")
    st.sidebar.markdown("---")

# --- CALENDAR SETUP ---
if "date_picker" not in st.session_state:
    st.session_state.date_picker = datetime.date.today()

selected_date = st.date_input("Select a date", key="date_picker")
date_str = str(selected_date)

# Reset state when date changes
if "last_date" not in st.session_state or st.session_state.last_date != date_str:
    st.session_state.last_date = date_str
    st.session_state.step = 1
    st.session_state.selected_photo = None

# ==========================
#       VIEW MODE
# ==========================
if date_str in db:
    entry = db[date_str]
    
    # 1. DISPLAY PHOTO (Priority: Local -> Cloud)
    local_path = entry.get("image_path")
    cloud_url = entry.get("image_url")
    
    st.caption(f"📅 Memory from {date_str}")

    # OPTION A: Try Local File First
    if local_path and os.path.exists(local_path):
        img_data = image_loader.load_image_for_streamlit(local_path)
        if img_data:
            st.image(img_data)
        else:
            st.error("⚠️ Local image file is corrupt.")
            
    # OPTION B: Fallback to Cloud URL
    elif cloud_url:
        st.info("☁️ Loading image from Cloud...")
        st.image(cloud_url)
        
    else:
        if local_path: 
            st.warning(f"⚠️ Photo missing from disk: {local_path}")

    # 2. Summary
    st.subheader("📝 Summary")
    st.markdown(entry["summary"])
    
    # 3. Audio
    st.subheader("🎧 Recording")
    if os.path.exists(entry["audio_path"]):
        st.audio(entry["audio_path"])
    else:
        st.error("Audio file missing.")

# ==========================
#      RECORD MODE
# ==========================
else:
    # --- STEP 1: PHOTO SELECTION ---
    if st.session_state.step == 1:
        st.info("Step 1: Choose a photo")
        
        # This will now use your robust 'mac_photos' module
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
            st.warning("No downloaded photos found for this date. (Check Photos app to ensure they are downloaded from iCloud)")
        
        st.markdown("---")
        if st.button("Skip / No Photo"):
            st.session_state.selected_photo = None
            st.session_state.step = 2
            st.rerun()

    # --- STEP 2: RECORDING ---
    elif st.session_state.step == 2:
        st.info("Step 2: Record your thoughts")
        
        if st.session_state.selected_photo:
            st.caption("Selected Photo:")
            preview = image_loader.load_image_for_streamlit(st.session_state.selected_photo)
            if preview:
                st.image(preview, width=150)

        audio_value = st.audio_input(f"Record for {date_str}")

        if audio_value:
            st.warning("Processing...")
            audio_bytes = audio_value.read()

            try:
                # 1. AI Summary
                summary = ai.summarize_audio(audio_bytes)
                
                # 2. Save Locally
                database.save_entry(
                    date_str, 
                    summary, 
                    audio_bytes, 
                    st.session_state.selected_photo
                )

                # 3. Save to Cloud (Supabase)
                # Reconstruct path logic
                saved_audio_path = f"recordings/{date_str}.wav"
                
                try:
                    cloud_db.save_to_cloud(date_str, summary, saved_audio_path, st.session_state.selected_photo)
                    st.toast("✅ Synced to Cloud!")
                except Exception as e:
                    st.warning(f"Saved locally, but Cloud Sync failed: {e}")
                
                st.success("Entry Saved!")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")
        
        #if st.button("⬅️ Change Photo"):
        #    st.session_state.step = 1
        #    st.rerun()