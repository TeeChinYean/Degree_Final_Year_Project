import cv2
from ultralytics import YOLO
import time
from collections import defaultdict, Counter
import supervision as sv
import keyboard
model = YOLO(r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\firstTrain\retrain2\weights\best.onnx",task='detect')
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

print("✅ Camera started. Press 'q' to quit.")

tracked_objects = set()
class_per_id = defaultdict(str)
    
fps_start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Failed to grab frame")
        break
    
    results = model.track(frame, persist=True, conf=0.3, iou=0.5)
    annotated_frame = frame.copy()

    fps_end_time = time.time()
    fps = 1 / (fps_end_time - fps_start_time)
    fps_start_time = fps_end_time
    fps_text = f"FPS: {fps:.2f}"
    cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

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
