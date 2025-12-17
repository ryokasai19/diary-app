import streamlit as st
import datetime
import os
# Import your custom modules
from modules import database, ai, mac_photos, image_loader

st.title("Chit Chat!😋")

# 1. Calendar Widget
selected_date = st.date_input("Select a date", datetime.date.today())
date_str = str(selected_date)

# 2. Load Data
db = database.load_db()

if date_str in db:
    # ==========================
    #      VIEW MODE
    # ==========================
    entry = db[date_str]
    st.success(f"Entry found for {date_str}")
    
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
    # ==========================
    #     RECORD MODE
    # ==========================
    st.info(f"No entry for {date_str}. Create one below.")
    
    # --- STEP 1: PHOTO SELECTION ---
    st.markdown("### 1. Select a Photo (Optional)")
    
    selected_photo_path = None # Default to None
    
    try:
        suggested_photos = mac_photos.get_photos_from_mac_library(selected_date)
    except Exception:
        st.warning("Could not access Photos Library.")
        suggested_photos = []

    if suggested_photos:
        st.caption(f"Found photos from {date_str}")
        
        # Display photos in a grid
        cols = st.columns(3)
        for idx, photo_path in enumerate(suggested_photos):
            # Load image safely
            img_data = image_loader.load_image_for_streamlit(photo_path)
            
            if img_data:
                with cols[idx % 3]:
                    st.image(img_data, use_container_width=True)
                    # Unique key for every checkbox
                    if st.checkbox("Select", key=f"p_{idx}"):
                        selected_photo_path = photo_path
    else:
        st.caption("No local photos found for this date.")

    # --- STEP 2: AUDIO RECORDING ---
    st.markdown("### 2. Record Audio")
    
    # Testing mode enabled (True) - Change to 'if selected_date == datetime.date.today():' later
    if True: 
        audio_value = st.audio_input(f"Record for {date_str}")

        if audio_value:
            st.warning("Processing...")
            audio_bytes = audio_value.read()

            try:
                # 1. Get AI Summary
                summary = ai.summarize_audio(audio_bytes)
                
                # 2. Save to Database (including the photo!)
                database.save_entry(date_str, summary, audio_bytes, selected_photo_path)
                
                st.success("Saved! Refreshing...")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")