import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

# 1. Configuration
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.title("🎙️ AI Voice Diary")
st.write("Click the mic to record your thoughts.")

# 2. The Recording UI (No separate script needed!)
# This creates a widget in the browser that records audio
audio_value = st.audio_input("Record")

if audio_value:
    # When the user stops recording, this block runs automatically
    st.info("⏳ Processing your audio...")

    try:
        # 3. Create a temporary file
        # Gemini needs a file on disk to read, so we save the recording briefly
        with open("temp_audio.wav", "wb") as f:
            f.write(audio_value.read())

        # 4. Upload to Gemini
        myfile = genai.upload_file("temp_audio.wav")
        
        # 5. Generate Summary
        model = genai.GenerativeModel("gemini-flash-latest")
        result = model.generate_content([
            "Listen to this audio and summarize the key points into a bulleted list. Be as concise as possible, maximum 5 bullet points. Don't use colons and categorize, just list the important things the speaker said. Where, what with whom, how they felt might be important.　Avoid referring to the speaker as they, just omit the pronouns or if necessary, use first person.", 
            myfile
        ])
        
        # 6. Display Result
        st.success("Summary Generated!")
        st.markdown(result.text)

    except Exception as e:
        st.error(f"Error: {e}")