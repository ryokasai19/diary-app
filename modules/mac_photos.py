import osxphotos
import datetime
import os

def get_photos_from_mac_library(target_date):
    """
    Fetches photos using Auto-Discovery.
    Fallbacks: Original -> Edited -> Derivative (Preview)
    """
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
                
                # --- STRATEGY 1: The Original (Best Quality) ---
                if p.path and os.path.exists(p.path):
                    valid_path = p.path
                
                # --- STRATEGY 2: The Edited Version ---
                elif p.path_edited and os.path.exists(p.path_edited):
                    valid_path = p.path_edited
                
                # --- STRATEGY 3: The Preview/Thumbnail (The Fix!) ---
                # If the original is missing (Path=None), grab the largest preview available
                else:
                    # 'path_derivatives' returns a list of preview paths. We take the last one (usually largest).
                    derivatives = p.path_derivatives
                    if derivatives:
                        # Find the first one that actually exists on disk
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