# import os
# import shutil
# import random

# # --- 設定路徑 ---
# office_base = "f:/Degree_Final_Year_Project/temp_official" # 官方數據源
# self_base = "f:/Degree_Final_Year_Project/balanced_dataset"    # 自定義數據源
# final_base = "f:/Degree_Final_Year_Project/Final_Dataset"  # 合併後的目的地

# # 類別偏移設定
# SELF_ID_OFFSET = 34

# def get_all_files(base_path, prefix=""):
#     """獲取目錄下所有的圖片及其對應標籤檔"""
#     data = []
#     # 遍歷所有的 split (train, val, test) 蒐集所有原始數據
#     for s in ["train", "val", "test"]:
#         img_dir = os.path.join(base_path, f"{prefix}{s}", "images", s if "official" in prefix else "")
#         if not os.path.exists(img_dir): continue
        
#         for f in os.listdir(img_dir):
#             if f.lower().endswith(('.jpg', '.png', '.jpeg')):
#                 img_path = os.path.join(img_dir, f)
#                 # 假設標籤資料夾與圖片資料夾平行
#                 lbl_dir = img_dir.replace("images", "labels")
#                 lbl_path = os.path.join(lbl_dir, os.path.splitext(f)[0] + ".txt")
#                 if os.path.exists(lbl_path):
#                     data.append((img_path, lbl_path))
#     return data

# def move_and_fix_labels(file_list, target_split, is_self_data):
#     """搬運檔案並修正 ID (如果是自定義數據)"""
#     dest_img_dir = os.path.join(final_base, target_split, "images")
#     dest_lbl_dir = os.path.join(final_base, target_split, "labels")
#     os.makedirs(dest_img_dir, exist_ok=True)
#     os.makedirs(dest_lbl_dir, exist_ok=True)

#     for img_src, lbl_src in file_list:
#         fname = os.path.basename(img_src)
#         lname = os.path.basename(lbl_src)
        
#         # 複製圖片
#         shutil.copy(img_src, os.path.join(dest_img_dir, fname))
        
#         # 處理標籤
#         if is_self_data:
#             with open(lbl_src, 'r') as f:
#                 lines = f.readlines()
#             with open(os.path.join(dest_lbl_dir, lname), 'w') as f:
#                 for line in lines:
#                     parts = line.split()
#                     if parts:
#                         parts[0] = str(int(parts[0]) + SELF_ID_OFFSET)
#                         f.write(" ".join(parts) + "\n")
#         else:
#             shutil.copy(lbl_src, os.path.join(dest_lbl_dir, lname))

# # --- 開始執行 ---
# if os.path.exists(final_base): shutil.rmtree(final_base) # 清空舊的合併目錄

# print("📦 正在蒐集所有原始數據...")
# office_files = get_all_files(office_base, prefix="official_")
# self_files = get_all_files(self_base)

# # 打亂順序
# random.shuffle(office_files)
# random.shuffle(self_files)

# def split_data(files, train_ratio=0.8):
#     size = int(len(files) * train_ratio)
#     return files[:size], files[size:]

# # 分配 80/20
# off_train, off_val = split_data(office_files)
# self_train, self_val = split_data(self_files)

# print("🚀 正在執行混合搬運與標籤偏移...")
# move_and_fix_labels(off_train, "train", is_self_data=False)
# move_and_fix_labels(off_val, "val", is_self_data=False)
# move_and_fix_labels(self_train, "train", is_self_data=True)
# move_and_fix_labels(self_val, "val", is_self_data=True)

# print(f"✅ 混合合併完成！\n位置：{final_base}")




import os

# --- 設定你的最終路徑 ---
final_base = "f:/Degree_Final_Year_Project/Balanced_V4_Final_v2"  # 這裡請替換成你的最終資料夾路徑
yaml_path = os.path.join(final_base, "data.yaml")

# --- 寫入完整類別定義 ---
yaml_content = f"""path: {final_base}
train: train/images
val: val/images
test: test/images

names:
  0: Aluminium_Can
  1: hand
  2: paper
  3: plastic
"""

if not os.path.exists(final_base):
    os.makedirs(final_base)

with open(yaml_path, "w", encoding="utf-8") as f:
    f.write(yaml_content)

print(f"✅ 已成功補齊 YAML 檔案：{yaml_path}")