from ultralytics import YOLO

# Load the model
model = YOLO(r"F:\Degree_Final_Year_Project\V4_Retrain\yolo12_balanced_final_v22\weights\best.pt")

# Export the model to ONNX format
model.export(format="onnx", dynamic=True, batch=1, simplify=True, half=True, optimize=True, opset=16) #16
# model.export(format="TensorRT")


# from torch import nn

# from ultralytics import YOLO

# # Load the classification model
# model = YOLO(r"F:\Degree_Final_Year_Project\pt\newPt\best.pt")

# # Add average pooling layer
# head = model.model.model[-1]
# pool = nn.Sequential(nn.AdaptiveAvgPool2d((1, 1)), nn.Flatten(start_dim=1))
# pool.f, pool.i = head.f, head.i
# model.model.model[-1] = pool

# # Export to TensorRT
# model.export(format="engine", half=True, dynamic=True, batch=32)