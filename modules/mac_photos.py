import sys
import os
import datetime

# --- 1. SAFE IMPORT ---
# Only import 'osxphotos' if we are actually on a Mac.
# This prevents the "ModuleNotFoundError" on the Linux Cloud server.
osxphotos = None
if sys.platform == "darwin":
    try:
        import osxphotos
    except ImportError:
        pass

def get_photos_from_mac_library(target_date):
    """
    Fetches photos using Auto-Discovery (Mac Only).
    Safe for Cloud: Returns empty list if not on Mac.
    """
    
    # --- 2. SAFETY CHECK ---
    # If we are NOT on a Mac, or if the library isn't installed, stop immediately.
    if sys.platform != "darwin" or osxphotos is None:
        return []

    # --- 3. YOUR ORIGINAL LOGIC (Restored) ---
    print(f"🔍 Searching for photos on: {target_date}...")
    
    try:
        # Auto-detect the system library
        db = osxphotos.PhotosDB()
        photos = db.photos(movies=False)
        
        matching_photos = []
        found_date_match = False
        
        for p in photos:
            # Check if date matches (Year-Month-Day)
            if p.date.date() == target_date:
                found_date_match = True
                valid_path = None
                
                # STRATEGY 1: The Original (Best Quality)
                if p.path and os.path.exists(p.path):
                    valid_path = p.path
                
                # STRATEGY 2: The Edited Version
                elif p.path_edited and os.path.exists(p.path_edited):
                    valid_path = p.path_edited
                
                # STRATEGY 3: The Preview/Thumbnail
                else:
                    derivatives = p.path_derivatives
                    if derivatives:
                        for derivative_path in reversed(derivatives):
                            if os.path.exists(derivative_path):
                                valid_path = derivative_path
                                print(f"  📸 Found Preview/Derivative: {valid_path}")
                                break
                
                # Final Decision
                if valid_path:
                    matching_photos.append(valid_path)
                else:
                    print(f"  ⚠️ Skipped: No Original, Edited, or Preview found for {p.uuid}")
        
        if not found_date_match:
            print("  ❌ No photos found matching this date.")
            
        return matching_photos

    except Exception as e:
        print(f"❌ Error accessing Photos Library: {e}")
        return []