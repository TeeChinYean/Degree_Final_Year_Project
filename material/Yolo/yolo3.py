import cv2
from ultralytics import YOLO
import time
import numpy as np
from collections import defaultdict, Counter
import supervision as sv
import keyboard
model = YOLO(r"F:\Degree_Final_Year_Project\pt\newPt\best.onnx",task='detect')
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

print("✅ Camera started. Press 'q' to quit.")

fps_prev_time = time.time()

tracked_objects = set()
class_per_id = defaultdict(str)
    
fps_prev_time = time.time()
frame_activated = True
def frame():
    frame_activated = not frame_activated
    
keyboard.add_hotkey('f',frame)

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Failed to grab frame")
        break
    
    
        
    results = model.track(frame, persist=True, conf=0.3, iou=0.5)
    annotated_frame = frame.copy()
    
    #not completed yet
    if frame_activated:
        now = time.time()
        fps = 1 / (now - fps_prev_time)
        fps_prev_time = now
        cv2.putText(annotated_frame, f"FPS: {fps:.2f}", (10, 30),cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    if results and len(results) > 0:
        result = results[0]  # first frame result
        detections = sv.Detections.from_ultralytics(result)

        if detections.tracker_id is not None:
            for xyxy, class_id, track_id in zip(
                detections.xyxy, detections.class_id, detections.tracker_id
            ):
                if track_id is None:
                    continue  # skip untracked boxes

                if track_id not in tracked_objects:
                    tracked_objects.add(track_id)
                    class_name = model.names[int(class_id)]
                    class_per_id[track_id] = class_name

        annotated_frame = result.plot()

    cv2.imshow("YOLO Tracking", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

if tracked_objects:
    print("\nSummary of unique tracked objects:")
    class_counts = Counter(class_per_id.values())
    for class_name, count in class_counts.items():
        print(f"{class_name}: {count}")
