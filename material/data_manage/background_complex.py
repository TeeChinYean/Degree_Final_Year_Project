import cv2
import os
import random
import glob
import numpy as np

class YOLODataAugmentor:
    def __init__(self, src_img_dir, src_txt_dir, bg_img_dir, out_dir, class_id=0):
        """
        初始化增強器。
        :param src_img_dir: 前景圖片目錄 (例如: dataset_foreground/images)
        :param src_txt_dir: 前景 YOLO 標籤目錄 (例如: dataset_foreground/labels, 用於獲取類別，此處預設使用統一 class_id)
        :param bg_img_dir: 背景圖片目錄 (例如: dataset_background)
        :param out_dir: 輸出目錄 (將建立 images 和 labels 子目錄)
        :param class_id: 前景目標的類別 ID (預設為 0, 因為我們通常從純背景開始貼一類物體)
        """
        self.src_img_dir = src_img_dir
        self.bg_img_dir = bg_img_dir
        self.out_img_dir = os.path.join(out_dir, "images")
        self.out_label_dir = os.path.join(out_dir, "labels")
        self.class_id = class_id

        # 建立輸出目錄
        os.makedirs(self.out_img_dir, exist_ok=True)
        os.makedirs(self.out_label_dir, exist_ok=True)

        # 獲取檔案清單
        self.src_images = glob.glob(os.path.join(src_img_dir, "*.jpg")) + \
                          glob.glob(os.path.join(src_img_dir, "*.png"))
        self.bg_images = glob.glob(os.path.join(bg_img_dir, "*.jpg")) + \
                         glob.glob(os.path.join(bg_img_dir, "*.png"))

        if not self.src_images or not self.bg_images:
            raise ValueError("Error: Source or background directory is empty or contains no images.")
        
        print(f"Initialized: {len(self.src_images)} foregrounds, {len(self.bg_images)} backgrounds found.")

    def get_random_transform(self, image):
        """對前景圖片進行幾何變換: 隨機縮放, 翻轉, 小幅度旋轉"""
        h, w = image.shape[:2]

        # 1. 隨機水平翻轉 (50% 機率)
        if random.random() > 0.5:
            image = cv2.flip(image, 1)

        # 2. 隨機小幅度旋轉 (例如: -15 到 15 度)
        angle = random.uniform(-15, 15)
        M_rot = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
        # 使用透明度填充旋轉後的空白區域 (如果是 PNG)
        image = cv2.warpAffine(image, M_rot, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))

        return image

    def generate_augmented_data(self, count=100, max_objects=3, scale_range=(0.1, 0.4)):
        """
        開始生成增強資料。
        :param count: 要生成的總圖片數量
        :param max_objects: 每張圖最多貼幾個前景
        :param scale_range: 前景縮放比例範圍 (相對於背景寬度)
        """
        for i in range(count):
            # 隨機挑選背景
            bg_path = random.choice(self.bg_images)
            bg = cv2.imread(bg_path)
            if bg is None: continue
            bg_h, bg_w = bg.shape[:2]

            # 初始化這張圖的 YOLO 標籤清單
            yolo_labels = []

            # 1. 決定這次要貼幾個物體 (1 到 max_objects 之間的隨機數)
            num_to_overlay = random.randint(1, max_objects)
            
            # 挑選前景 (允許重複)
            selected_srcs = [random.choice(self.src_images) for _ in range(num_to_overlay)]

            # 用於生成檔名的基礎名稱
            base_name = f"aug_{i:05d}"

            for src_path in selected_srcs:
                # 讀取前景 (嘗試讀取 Alpha 通道)
                src = cv2.imread(src_path, cv2.IMREAD_UNCHANGED)
                if src is None: continue

                # 應用幾何變換
                src = self.get_random_transform(src)
                
                src_h, src_w = src.shape[:2]

                # 2. 隨機縮放 (相對於背景寬度)
                scale = random.uniform(scale_range[0], scale_range[1])
                new_w = int(bg_w * scale)
                # 保持長寬比
                new_h = int(src_h * (new_w / src_w))
                
                # 防止前景過大 (雖然很少見)
                if new_h > bg_h:
                    new_h = bg_h
                    new_w = int(src_w * (new_h / src_h))
                
                src_resized = cv2.resize(src, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

                # 3. 隨機產生放置位置 (確保不會超出邊界)
                max_x = bg_w - new_w
                max_y = bg_h - new_h
                x = random.randint(0, max_x)
                y = random.randint(0, max_y)

                # 4. 執行融合 (在此腳本中使用基本的透明度融合或直接覆蓋)
                # 我們假設前景可能是 PNG 且有 Alpha 通道
                if src_resized.shape[2] == 4:
                    # PNG 透明度融合
                    alpha_src = src_resized[:, :, 3] / 255.0
                    alpha_bg = 1.0 - alpha_src
                    for c in range(0, 3):
                        bg[y:y+new_h, x:x+new_w, c] = (alpha_src * src_resized[:, :, c] +
                                                      alpha_bg * bg[y:y+new_h, x:x+new_w, c])
                else:
                    # JPG 直接覆蓋
                    bg[y:y+new_h, x:x+new_w] = src_resized[:, :, :3]

                # 5. 計算並儲存 YOLO 標籤 (歸一化座標)
                x_center = (x + new_w / 2) / bg_w
                y_center = (y + new_h / 2) / bg_h
                norm_w = new_w / bg_w
                norm_h = new_h / bg_h
                
                yolo_labels.append(f"{self.class_id} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")

            # 6. 儲存圖片
            img_out_path = os.path.join(self.out_img_dir, f"{base_name}.jpg")
            cv2.imwrite(img_out_path, bg)

            # 7. 儲存標籤檔 (.txt)
            label_out_path = os.path.join(self.out_label_dir, f"{base_name}.txt")
            with open(label_out_path, 'w') as f:
                f.write('\n'.join(yolo_labels))

            if (i+1) % 10 == 0:
                print(f"Processed: {i+1}/{count} images...")

        print(f"Successfully generated {count} augmented images and labels in '{out_dir}'.")

# ==========================================
# 使用範例 (在此修改你的路徑)
# ==========================================

# 假設你的資料夾結構如下：
# dataset_foreground/
#   images/ (放 JPG/PNG 圖片)
# dataset_background/ (放純背景 JPG 圖片)
# output_augmented/ (腳本會自動建立此目錄，內含 images 和 labels)

# 請修改以下路徑為你電腦上的真實路徑
FOREGROUND_IMG_DIR = "path/to/dataset_foreground/images" # 改這裡
BACKGROUND_IMG_DIR = "path/to/dataset_background"       # 改這裡
OUTPUT_DIR = "path/to/output_augmented"                 # 改這裡

try:
    augmentor = YOLODataAugmentor(
        src_img_dir=FOREGROUND_IMG_DIR,
        src_txt_dir="", # 此範例腳本預設統一 class_id, 不需前景標籤
        bg_img_dir=BACKGROUND_IMG_DIR,
        out_dir=OUTPUT_DIR,
        class_id=0 # 假設你要偵測的貓是 class 0
    )

    # 生成 200 張圖片，每張隨機貼 1~4 個貓，縮放比例為背景寬度的 15% 到 35%
    augmentor.generate_augmented_data(count=200, max_objects=4, scale_range=(0.15, 0.35))

except ValueError as e:
    print(e)
except Exception as e:
    print(f"An unexpected error occurred: {e}")