import pillow_heif
from PIL import Image
import os



def load_image_for_streamlit(path):
    """
    Safely loads an image from a path. 
    Handles HEIC conversion and checks for corruption.
    Returns a PIL Image object or None if the file is bad.
    """
    if not os.path.exists(path):
        return None

    try:
        # 1. Handle HEIC Files (iPhone)
        if path.lower().endswith(".heic"):
            heif_file = pillow_heif.read_heif(path)
            image = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
            )
            return image
            
        # 2. Handle Standard Files (JPG, PNG, etc.)
        else:
            # We explicitly open it here to catch corruption errors 
            # before passing it to Streamlit.
            image = Image.open(path)
            image.load() # Force loading the image data to check for errors
            return image

    except Exception as e:
        # If anything goes wrong (corrupted file, 0 bytes, etc.), return None
        print(f"⚠️ Warning: Could not load image at {path}: {e}")
        return None