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
        model = genai.GenerativeModel("gemini-flash-latest")
        result = model.generate_content([
            "Listen to this audio and summarize the key points into a bulleted list. Be as concise as possible, maximum 5 bullet points. Don't use colons and categorize, just list the important things the speaker said. Where, what with whom, how they felt might be important.　Avoid referring to the speaker as they, just omit the pronouns or if necessary, use first person.", 
            myfile
        ])
        
        # Cleanup (Optional but good practice)
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return result.text

    except Exception as e:
        # Re-raise the error so the UI knows something went wrong
        raise e