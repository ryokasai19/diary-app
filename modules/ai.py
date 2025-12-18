import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load keys once when this module is imported
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def summarize_audio(audio_bytes):
    """Uploads audio bytes to Gemini and returns the summary text."""
    try:
        # Save temp file for upload
        temp_path = "temp_upload.wav"
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)
        
        # Upload
        myfile = genai.upload_file(temp_path)
        
        # Generate
        model = genai.GenerativeModel("gemini-2.0-flash")
        result = model.generate_content([
            """
            Summarize this audio into a concise bulleted list (max 5 points).
            Style: Telegraphic, first-person diary format.
            Just output the bullet points, nothing like 'Okay, here is the summary in telegraphic, first-person diary format:' needed.
            - Focus on: Who, What, Where, How.
            - Grammar: Use sentence fragments. Omit "they/he/she". Use "I" if needed.
            - Example: "Met Nicholas. He is moving to Seattle" -> "Nicholas moving to Seattle."

            Required Final Bullet:
            - A subjective 2-3 word description of the speaker's vibe (e.g., 'Sounded drunk', 'Sounded excited', 'Voice cracked').
            """,
            myfile
        ])
        
        # Cleanup (Optional but good practice)
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return result.text

    except Exception as e:
        # Re-raise the error so the UI knows something went wrong
        raise e