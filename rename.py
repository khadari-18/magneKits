import os

def rename_images(folder_path, prefix="fc2_save_2026-09-27-193922-0004.jpg_2026-09-27-194805-"):
    # Supported image extensions
    valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
    
    # Get all files and sort them to keep a consistent order
    files = sorted(os.listdir(folder_path))
    
    image_count = 1
    for filename in files:
        ext = os.path.splitext(filename)[1].lower()
        if ext in valid_extensions:
            old_path = os.path.join(folder_path, filename)
            
            # Format number with leading zeros (e.g., 001, 002)
            new_name = f"{prefix}_{str(image_count).zfill(4)}{ext}"
            new_path = os.path.join(folder_path, new_name)
            
            os.rename(old_path, new_path)
            image_count += 1

    print(f"Successfully renamed {image_count - 1} images!")

# Replace with your actual folder path
folder_location = r"/Volumes/Data Drive/RESEARCH-UNC/uRheo Data/3DFM Data/HA/Compliance_0.1pct_2p8umPEG/Set2_3v_30s"
rename_images(folder_location, prefix="img")

