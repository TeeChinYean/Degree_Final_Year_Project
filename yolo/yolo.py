import cv2
from ultralytics import YOLO
import time
import numpy as np
import torch

import threading

def backend():
    
# model = YOLO(r'F:\Degree_Final_Year_Project\runs\detect\fine2\train2\weights\best.pt')
model = YOLO(r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\secondTrain\Extra_retrain2\weights\best.onnx")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

print("✅ Camera started. Press 'q' to quit.")

fps_start_time = time.time()

while True:    
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Failed to grab frame")
        break
    
    fps_end_time = time.time()
    fps = 1 / (fps_end_time - fps_start_time)
    fps_start_time = fps_end_time
    fps_text = f"FPS: {fps:.2f}"
    cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)


    # Run YOLO detection
    results = model.track(frame, stream=True,persist=True,conf=0.3, iou=0.5,tracker="botsort.yaml",device='cuda' if torch.cuda.is_available() else 'cpu')
    
    # Draw results on the frame
    for r in results:
        annotated_frame = r.plot()  # draws boxes and labels

    # Display the frame
    cv2.imshow("Detection", annotated_frame)

    box = np.zeros((512,512,3), np.uint8)

    start_point = (0,0)
    end_point = (511,511)
    color = (255,255,255)
    thickness = 5

    cv2.line(box, start_point, end_point, color, thickness)
    
    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release camera and close window
cap.release()
cv2.destroyAllWindows()
