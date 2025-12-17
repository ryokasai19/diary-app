from PIL import Image, ImageOps
import os

def load_image_for_streamlit(image_path):
    """
    Loads an image from a path, corrects its orientation (EXIF),
    and returns a PIL Image object ready for st.image().
    Returns None if the file cannot be read.
    """
    if not image_path or not os.path.exists(image_path):
        return None

    try:
        image = Image.open(image_path)
        
        # fix orientation (iPhone photos often appear rotated otherwise)
        image = ImageOps.exif_transpose(image)
        
        return image
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None