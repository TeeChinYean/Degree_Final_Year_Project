# import fiftyone as fo
# import fiftyone.zoo as foz
# import fiftyone.utils.random as four
# import os

# # 1. 設定導出路徑
# export_dir = "f:/Degree_Final_Year_Project/official_data"

# # 2. 定義 30 個官方類別
# selected_classes = [
#     "person", "backpack", "umbrella", "handbag", "tie", "suitcase",
#     "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", 
#     "microwave", "oven", "sink", "refrigerator",
#     "banana", "apple", "sandwich", "orange", "pizza", "donut", "cake",
#     "tv", "laptop", "mouse", "remote", "keyboard", "cell phone"
# ]

# print("正在從 COCO Zoo 下載並加載數據 (包含自動續傳)...")

# # 3. 下載數據集
# # 注意：如果你剛才下載到一半，這行代碼會自動從上次斷掉的地方繼續
# dataset = foz.load_zoo_dataset(
#     "coco-2017",
#     split="train",
#     label_types=["detections"],
#     classes=selected_classes,
#     max_samples=3000,
#     num_workers=8  # 建議設為 2 比較穩定，避免連線再次中斷
# )

# # 4. 執行三路隨機切分 (7:2:1 比例)
# # 這是學術論文最標準的劃分方式
# print("正在執行數據切分 (Train: 0.7, Val: 0.2, Test: 0.1)...")
# four.random_split(dataset, {"train": 0.7, "val": 0.2, "test": 0.1})

# # 5. 執行導出
# print(f"正在將數據導出至: {export_dir}")
# # 循環處理三個 split
# for split in ["train", "val", "test"]:
#     view = dataset.match_tags(split)
#     view.export(
#         export_dir=export_dir,
#         dataset_type=fo.types.YOLOv5Dataset,
#         label_field="ground_truth",
#         split=split,
#         classes=selected_classes,
#         overwrite=True
#     )

# print("✅ 官方數據 (Train/Val/Test) 重新下載並導出完成！")



import fiftyone as fo
import fiftyone.zoo as foz
import fiftyone.utils.random as four
import os

# 1. 載入數據
dataset = foz.load_zoo_dataset("coco-2017", split="train", max_samples=3000)

selected_classes = [
    "person", "backpack", "umbrella", "handbag", "tie", "suitcase",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", 
    "microwave", "oven", "sink", "refrigerator",
    "banana", "apple", "sandwich", "orange", "pizza", "donut", "cake",
    "tv", "laptop", "mouse", "remote", "keyboard", "cell phone"
]

# 2. 重新切分
four.random_split(dataset, {"train": 0.7, "val": 0.2, "test": 0.1})

# 3. 分路徑導出 (核心修復)
base_path = "f:/Degree_Final_Year_Project/temp_official"

for s in ["train", "val", "test"]:
    print(f"正在導出至獨立資料夾: {s}...")
    view = dataset.match_tags(s)
    
    # 強制將路徑分開，防止 FiftyOne 刪除前一個資料夾
    individual_export_dir = os.path.join(base_path, f"official_{s}")
    
    view.export(
        export_dir=individual_export_dir,
        dataset_type=fo.types.YOLOv5Dataset,
        label_field="ground_truth",
        classes=selected_classes,
        overwrite=True
    )

print(f"✅ 導出完成！請前往 {base_path} 查看。")