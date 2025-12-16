import streamlit as st
import datetime
# Import your new custom modules
from modules import database, ai

st.title("📅 AI Voice Calendar")

# 1. Calendar Widget
selected_date = st.date_input("Select a date", datetime.date.today())
date_str = str(selected_date)

# 2. Load Data
db = database.load_db()

if date_str in db:
    # --- VIEW MODE ---
    entry = db[date_str]
    st.success(f"Entry found for {date_str}")
    st.subheader("📝 Summary")
    st.markdown(entry["summary"])
    st.subheader("🎧 Recording")
    st.audio(entry["audio_path"])

else:
    # --- RECORD MODE ---
    st.info(f"No entry for {date_str}.")
    
    # !!! change this part to record only if the date is today !!!
    # if selected_date == datetime.date.today():
    if True:
        audio_value = st.audio_input("Record your day")

        if audio_value:
            st.warning("Processing...")
            audio_bytes = audio_value.read()

            try:
                # Call the AI module
                summary = ai.summarize_audio(audio_bytes)
                
                # Call the Database module
                database.save_entry(date_str, summary, audio_bytes)
                
                st.success("Saved! Refreshing...")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")