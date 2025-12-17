import streamlit as st
import datetime
import os
# Import your custom modules
from modules import database, ai, mac_photos, image_loader

st.title("Chit Chat!😋")

# Load Data first (needed for search functionality)
db = database.load_db()

# --- SEARCH SIDEBAR ---
st.sidebar.header("🔍 Search Memories")
search_term = st.sidebar.text_input("Find keyword")

# Define a tiny helper function to update the calendar
def go_to_date(new_date):
    st.session_state.date_picker = new_date

if search_term:
    results = [d for d, data in db.items() if search_term.lower() in data["summary"].lower()]
    
    st.sidebar.markdown(f"**Found {len(results)} entries:**")
    
    for date_result in results:
        # Convert string "2025-12-16" back to a Date Object
        y, m, d = map(int, date_result.split("-"))
        target_date = datetime.date(y, m, d)

        # BUTTON with 'on_click' (This is the magic fix)
        st.sidebar.button(
            f"📅 {date_result}", 
            key=f"btn_search_{date_result}",
            on_click=go_to_date,  # <--- Triggers the function immediately
            args=(target_date,)   # <--- Passes the date to the function
        )

    if not results:
        st.sidebar.caption("No matches found.")
    st.sidebar.markdown("---")

# 1. Calendar Widget
# --- FIX: Initialize the date in session state first ---
if "date_picker" not in st.session_state:
    st.session_state.date_picker = datetime.date.today()

# Now create the widget WITHOUT a default value argument
# It will automatically use whatever is in st.session_state.date_picker
selected_date = st.date_input("Select a date", key="date_picker")
date_str = str(selected_date)
# --- NEW: Session State Setup ---
if "last_date" not in st.session_state or st.session_state.last_date != date_str:
    st.session_state.last_date = date_str
    st.session_state.step = 1            # Start at Step 1 (Photos)
    st.session_state.selected_photo = None # Reset photo

if date_str in db:
    # ==========================
    #      VIEW MODE
    # ==========================
    entry = db[date_str]
    #st.success(f"Entry found for {date_str}")
    
    # 1. Display Photo with Diagnostics
    saved_path = entry.get("image_path")

    if saved_path: 
        if os.path.exists(saved_path):
            # --- DEBUG CHECK 2: try to load ---
            try:
                img_data = image_loader.load_image_for_streamlit(saved_path)
                
                if img_data:
                    st.image(img_data, use_container_width=True)
                else:
                    st.error("❌ Error: The image loader returned 'None'. The file might be corrupted or empty.")
            except Exception as e:
                st.error(f"❌ Crash in loader: {e}")
        else:
            st.error(f"❌ Error: File not found at `{saved_path}`. Check your 'image_path' folder.")
            
    # 2. Display Summary
    st.subheader("📝 Summary")
    st.markdown(entry["summary"])
    
    # 3. Display Recording
    st.subheader("🎧 Recording")
    st.audio(entry["audio_path"])

else:
    # --- STEP 1: PHOTO SELECTION ---
    if st.session_state.step == 1:
        st.info("Step 1: Choose a photo")
        
        try:
            suggested_photos = mac_photos.get_photos_from_mac_library(selected_date)
        except Exception:
            suggested_photos = []

        if suggested_photos:
            cols = st.columns(3)
            for idx, photo_path in enumerate(suggested_photos):
                img_data = image_loader.load_image_for_streamlit(photo_path)
                
                if img_data:
                    with cols[idx % 3]:
                        st.image(img_data, use_container_width=True)
                        # BUTTON: Selects and moves to next step
                        if st.button("Select", key=f"btn_{idx}"):
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

    # --- STEP 2: AUDIO RECORDING ---
    elif st.session_state.step == 2:
        st.info("Step 2: Record your thoughts")
        
        # Show Preview
        if st.session_state.selected_photo:
            st.caption("Selected Photo:")
            preview = image_loader.load_image_for_streamlit(st.session_state.selected_photo)
            if preview:
                st.image(preview, width=150)

        # Recorder
        audio_value = st.audio_input(f"Record for {date_str}")

        if audio_value:
            st.warning("Processing...")
            audio_bytes = audio_value.read()

            try:
                summary = ai.summarize_audio(audio_bytes)
                
                # Save using the stored photo path
                database.save_entry(
                    date_str, 
                    summary, 
                    audio_bytes, 
                    st.session_state.selected_photo
                )
                
                st.success("Saved!")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

        # I don't think it's needed        
        # Back Button
        #if st.button("⬅️ Change Photo"):
        #    st.session_state.step = 1
        #    st.rerun()