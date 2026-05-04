import os
import random
import shutil
from collections import Counter

# --- 修改為你新下載的路徑 ---
BASE_SRC = r"f:\Degree_Final_Year_Project\Balanced_V4_Final"
# 現在包含了 'val'，從三個資料夾中提取所有數據進行重新分配
SUB_FOLDERS = ['train', 'val', 'test'] 

# --- 輸出路徑 ---
DEST_ROOT = r"f:\Degree_Final_Year_Project\Balanced_V4_Final_v2"

# --- 終極平衡參數 ---
# 這將確保每個類別在訓練、驗證、測試中都有固定的、相等的份額
LIMITS = {"train": 1000, "val": 200, "test": 120}

# 支援 0-3 或 34-37 兩種 ID 格式，確保代碼更具兼容性
ID_MAP = {
    "0": "Aluminium_Can",
    "1": "hand",          
    "2": "paper",         
    "3": "plastic",       
}

def prepare_folders():
    for split in LIMITS.keys():
        os.makedirs(os.path.join(DEST_ROOT, split, "images"), exist_ok=True)
        os.makedirs(os.path.join(DEST_ROOT, split, "labels"), exist_ok=True)

def get_file_category(label_path):
    try:
        with open(label_path, 'r') as f:
            line = f.readline()
            if line: return line.split()[0]
    except: return None
    return None

def main():
    prepare_folders()
    print(f"🔍 正在從 {SUB_FOLDERS} 蒐集並分類所有原始數據...")
    files_by_cat = {name: [] for name in set(ID_MAP.values())}
    
    for sub in SUB_FOLDERS:
        img_dir = os.path.join(BASE_SRC, sub, "images")
        lbl_dir = os.path.join(BASE_SRC, sub, "labels")
        if not os.path.exists(img_dir): continue
        
        imgs = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        for img_name in imgs:
            name_no_ext = os.path.splitext(img_name)[0]
            lbl_path = os.path.join(lbl_dir, name_no_ext + ".txt")
            
            cid = get_file_category(lbl_path)
            if cid in ID_MAP:
                cat_name = ID_MAP[cid]
                files_by_cat[cat_name].append({
                    "name": name_no_ext,
                    "img": os.path.join(img_dir, img_name),
                    "lbl": lbl_path
                })

    print("-" * 30)
    for cat_name, all_data in files_by_cat.items():
        random.shuffle(all_data)
        
        t_end = min(len(all_data), LIMITS['train'])
        v_end = min(len(all_data), t_end + LIMITS['val'])
        te_end = min(len(all_data), v_end + LIMITS['test'])
        
        splits = {
            "train": all_data[:t_end], 
            "val": all_data[t_end:v_end], 
            "test": all_data[v_end:te_end]
        }
        
        print(f"{cat_name:<15}: Train:{len(splits['train'])} Val:{len(splits['val'])} Test:{len(splits['test'])}")

        for s_name, data_list in splits.items():
            for item in data_list:
                # 複製圖片
                shutil.copy(item['img'], os.path.join(DEST_ROOT, s_name, "images"))
                
                # 同步處理標籤 ID (確保輸出一定是 0, 1, 2, 3)
                with open(item['lbl'], 'r') as f:
                    lines = f.readlines()
                
                new_lbl_path = os.path.join(DEST_ROOT, s_name, "labels", item['name'] + ".txt")
                with open(new_lbl_path, 'w') as f:
                    for line in lines:
                        parts = line.split()
                        if parts:
                            old_id = int(parts[0])
                            new_id = old_id - 34 if old_id >= 34 else old_id
                            parts[0] = str(new_id)
                            f.write(" ".join(parts) + "\n")

    print(f"\n✅ 全自動平衡切分完成！新數據集: {DEST_ROOT}")

if __name__ == "__main__":
    main()