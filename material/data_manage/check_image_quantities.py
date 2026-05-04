import os
import yaml
from collections import Counter
from pathlib import Path

# --- Configuration ---
DATA_YAML_PATH = "F:/Degree_Final_Year_Project/resized_dataset/data.yaml"

def resolve_label_dir(root_path, split_rel_path, split):
    split_path = Path(split_rel_path)

    # YOLO default: train: train/images -> labels in train/labels
    if split_path.parts and split_path.parts[-1] == "images":
        candidate = root_path / split_path.parent / "labels"
        if candidate.exists():
            return candidate

    # Alternate layouts used in some datasets/tools
    fallback_candidates = [
        root_path / split / "labels",
        root_path / "labels" / split,
        root_path / split_path.parent / "labels",
        root_path / split_path / "labels",
    ]
    for candidate in fallback_candidates:
        if candidate.exists():
            return candidate

    # Return best-effort default for error printing
    if split_path.parts and split_path.parts[-1] == "images":
        return root_path / split_path.parent / "labels"
    return root_path / split / "labels"

def count_dataset_classes(yaml_path):
    # 1. Load YAML safely
    yaml_file = Path(yaml_path)
    if not yaml_file.exists():
        print(f"❌ Error: YAML file not found at {yaml_path}")
        return

    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # 2. Resolve root path logic
    # Fallback to the directory containing the YAML if 'path' is missing
    root_path = data.get('path')
    if root_path:
        root_path = Path(root_path)
    else:
        root_path = yaml_file.parent
        print(f"ℹ️ 'path' key not found in YAML. Using YAML directory: {root_path}")

    names = data.get('names', {})
    splits = ['train', 'val', 'test']
    
    print(f"\n🔍 Statistics for Dataset: {root_path.absolute()}")
    print("=" * 60)

    for split in splits:
        # Check if the split path is defined in YAML (e.g., train: images/train)
        split_rel_path = data.get(split)
        if not split_rel_path:
            print(f"⚠️ Split '{split}' not defined in YAML. Skipping.")
            continue

        label_dir = resolve_label_dir(root_path, split_rel_path, split)

        if not label_dir.exists():
            print(f"⚠️ Labels directory not found for {split}: {label_dir}")
            continue

        class_counts = Counter()
        file_count = 0

        # 3. Process label files
        label_files = list(label_dir.glob("*.txt"))
        file_count = len(label_files)

        for label_file in label_files:
            with open(label_file, 'r') as f:
                for line in f:
                    parts = line.split()
                    if parts:
                        try:
                            class_id = int(parts[0])
                            class_counts[class_id] += 1
                        except ValueError:
                            continue # Skip corrupted lines

        # 4. Display Results
        print(f"\n📂 Split: [{split.upper()}] | Total Images: {file_count}")
        if file_count == 0:
            print("   No labels found.")
            continue

        print(f"{'ID':<5} {'Class Name':<25} {'Instances':<10}")
        print("-" * 50)
        
        for cid in sorted(names.keys() if isinstance(names, dict) else range(len(names))):
            cname = names[cid] if isinstance(names, dict) else names[cid]
            count = class_counts.get(cid, 0)
            print(f"{cid:<5} {cname:<25} {count:<10}")

if __name__ == "__main__":
    count_dataset_classes(DATA_YAML_PATH)




# # clean image

# import os
# import shutil
# from pathlib import Path
# from collections import Counter

# # --- 設定路徑 ---
# SOURCE_DIR = Path("f:/Degree_Final_Year_Project/self_dataset")
# TARGET_DIR = Path("f:/Degree_Final_Year_Project/balanced_dataset")
# LIMIT = 1400  # 每個類別的最大數量
# SPLITS = ['train', 'val', 'test']  # 包含所有分割區

# def balance_dataset():
#     print(f"🚀 開始平衡數據集，目標上限：{LIMIT}")
    
#     for split in SPLITS:
#         img_dir = SOURCE_DIR / split / 'images'
#         lbl_dir = SOURCE_DIR / split / 'labels'
        
#         # 檢查目錄是否存在，不存在則跳過
#         if not lbl_dir.exists() or not img_dir.exists():
#             print(f"ℹ️ 跳過 {split}：找不到目錄。")
#             continue

#         # 創建新的目標目錄
#         (TARGET_DIR / split / 'images').mkdir(parents=True, exist_ok=True)
#         (TARGET_DIR / split / 'labels').mkdir(parents=True, exist_ok=True)

#         # 1. 讀取並記錄標籤信息
#         file_map = {}
#         for lbl_file in lbl_dir.glob("*.txt"):
#             with open(lbl_file, 'r') as f:
#                 # 獲取該文件中所有的類別 ID
#                 classes = [int(line.split()[0]) for line in f.readlines() if line.split()]
#                 file_map[lbl_file.stem] = classes

#         # 2. 篩選圖片
#         current_counts = Counter()
#         selected_files = []

#         # 按包含物體數量由少到多排序（有助於精確控制數量）
#         sorted_filenames = sorted(file_map.keys(), key=lambda x: len(file_map[x]))

#         for fname in sorted_filenames:
#             classes_in_file = file_map[fname]
            
#             # 檢查加入此圖後，是否會使任何一個類別超過上限
#             can_add = True
#             for cls in classes_in_file:
#                 if current_counts[cls] >= LIMIT:
#                     can_add = False
#                     break
            
#             if can_add:
#                 selected_files.append(fname)
#                 for cls in classes_in_file:
#                     current_counts[cls] += 1

#         # 3. 執行文件複製
#         print(f"\n📂 正在處理 [{split.upper()}] 分割區...")
#         for fname in selected_files:
#             # 複製標籤檔
#             shutil.copy(lbl_dir / f"{fname}.txt", TARGET_DIR / split / 'labels' / f"{fname}.txt")
            
#             # 複製對應的圖片檔 (支援多種格式)
#             found_img = False
#             for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
#                 img_path = img_dir / f"{fname}{ext}"
#                 if img_path.exists():
#                     shutil.copy(img_path, TARGET_DIR / split / 'images' / f"{fname}{ext}")
#                     found_img = True
#                     break
#             if not found_img:
#                 print(f"⚠️ 警告：找不到 {fname} 的對應圖片")

#         # 打印最終統計
#         print(f"✅ {split} 處理完成。實際數量：{dict(sorted(current_counts.items()))}")

# if __name__ == "__main__":
#     balance_dataset()
#     print(f"\n✨ 平衡後的數據集已保存至: {TARGET_DIR}")