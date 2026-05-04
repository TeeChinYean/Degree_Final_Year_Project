# from ultralytics import YOLO
# import tensorrt as trt

# model = YOLO(r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\secondTrain\Extra_retrain2\weights\best.pt")

# model.export(
#     format="engine",      # TensorRT
#     device=0,             # GPU
#     half=True,            # FP16 (recommended)
#     dynamic=False,        # static shape is faster
#     imgsz=640,            # your model input size
#     workspace=2,         # workspace size in GB (default 16GB
# )


from ultralytics import YOLO
# 重新加载 .pt 并导出为 FP16 的 engine
model = YOLO(r'F:\Degree_Final_Year_Project\V4_Retrain\yolo12_balanced_final_v22\weights\best.pt') 
model.export(format='engine', imgsz=640, half=True, device=0, dynamic=False, int8=True, simplify=True)
  # 导出为 TensorRT engine，使用 FP16，静态输入大小，工作空间 2GB