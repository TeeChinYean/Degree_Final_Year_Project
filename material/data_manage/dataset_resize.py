import os
import shutil
from pathlib import Path
from PIL import Image

# --- Configuration ---
SOURCE_DIR = Path("f:/Degree_Final_Year_Project/Balanced_V4_Final_v2")  # dataset root
TARGET_DIR = Path("f:/Degree_Final_Year_Project/resized_dataset") # output root
SIZE = (320, 320)  # target resolution (width, height)
SPLITS = ['train', 'val', 'test']  # dataset splits

def resize_images():
    print(f"[INFO] Resizing all images to {SIZE[0]}x{SIZE[1]} pixels")

    for split in SPLITS:
        img_dir = SOURCE_DIR / split / 'images'
        lbl_dir = SOURCE_DIR / split / 'labels'
        if not img_dir.exists():
            print(f"[INFO] Skipping {split}: no images directory found.")
            continue

        # Create target directory
        target_img_dir = TARGET_DIR / split / 'images'
        target_lbl_dir = TARGET_DIR / split / 'labels'
        target_img_dir.mkdir(parents=True, exist_ok=True)
        target_lbl_dir.mkdir(parents=True, exist_ok=True)

        # Process images
        resized_count = 0
        copied_labels = 0
        for img_file in img_dir.glob("*.*"):
            try:
                with Image.open(img_file) as img:
                    # Convert to RGB to avoid issues with PNG/alpha channels
                    img = img.convert("RGB")
                    # Use modern resampling method
                    img_resized = img.resize(SIZE, Image.Resampling.LANCZOS)

                    # Save to target directory with same filename
                    save_path = target_img_dir / img_file.name
                    img_resized.save(save_path, quality=95)
                    resized_count += 1

                # Copy YOLO label file if present (same stem as image name)
                src_label = lbl_dir / f"{img_file.stem}.txt"
                if src_label.exists():
                    shutil.copy2(src_label, target_lbl_dir / src_label.name)
                    copied_labels += 1
            except Exception as e:
                print(f"[WARN] Error processing {img_file.name}: {e}")

        print(
            f"[OK] Finished {split} split -> {target_img_dir} "
            f"(images: {resized_count}, labels: {copied_labels})"
        )

if __name__ == "__main__":
    resize_images()
    print(f"\n[OK] Resized dataset saved to: {TARGET_DIR}")
