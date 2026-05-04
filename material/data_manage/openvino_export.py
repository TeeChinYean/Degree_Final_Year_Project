from ultralytics import YOLO

# 1. 載入你訓練好的最佳模型
model = YOLO(r'F:\Degree_Final_Year_Project\V4_Retrain\320p_yolo5\weights\best.pt')  # 替換成你的模型路徑

# 2. 針對 Ryzen 5 7535HS 進行最佳化導出
# 我們選擇 FP16，因為它是 Radeon 660M iGPU 效率最高的格式
path = model.export(
    format='openvino',
    imgsz=320,          # 保持與訓練一致
    half=True,          # 使用 FP16 半精度，能顯著提升 iGPU 效能並減少內存佔用
    int8=False,         # 除非有特定極低功耗需求，否則 FP16 在這顆 CPU 上平衡感最好
    dynamic=True,       # 開啟動態維度，適應不同的輸入 batch 
    simplify=True,       # 簡化網絡結構，移除不必要的算子
    optimize=True,       # 啟用 OpenVINO 的優化器，針對 CPU 進行性能調整
    opset=16            # 使用最新的 ONNX opset 以獲得最佳兼容性和性能
)

print(f"✅ OpenVINO 模型已導出至: {path}")