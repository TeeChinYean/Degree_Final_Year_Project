from ultralytics import YOLO
model = YOLO(r"F:\Degree_Final_Year_Project\runs\best.onnx")
print(model.names)
