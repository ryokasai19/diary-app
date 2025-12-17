import os
import osxphotos
from datetime import date

def get_photos_from_mac_library(target_date):
    """
    Queries the default Mac Photos Library for photos taken on target_date.
    Returns a list of full file paths to the images.
    """
    try:
        # Load the Photos Database (this might take a second the first time)
        photos_db = osxphotos.PhotosDB()
        
        matches = []
        for photo in photos_db.photos():
            # Check if the photo is not in the Trash and matches the date
            if not photo.intrash and photo.date.date() == target_date:
                # We only want photos that are actually downloaded to the Mac (not just in iCloud)
                if photo.path and os.path.exists(photo.path):
                    matches.append(photo.path)
        
        return matches
        
    except Exception as e:
        print(f"Error accessing Photos Library: {e}")
        return []

