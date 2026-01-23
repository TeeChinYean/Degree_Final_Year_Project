import cv2
import supervision as sv
import ultralytics as ul 
from collections import defaultdict
from collections import Counter
from ultralytics import YOLO

model = ul.YOLO(r'F:\Degree_Final_Year_Project\runs\detect\fine\train6\weights\best.pt')
# model = YOLO(r"F:\Degree_Final_Year_Project\runs\detect\train3\weights\best.onnx")
# Initialize annotators
bounding_box_annotator = sv.BoxAnnotator()
label_annotator = sv.LabelAnnotator()

# Initialize object tracker (ByteTrack)
tracker = sv.ByteTrack()

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Record of unique tracked objects
tracked_objects = set()
class_per_id = defaultdict(str)

print("Tracking script started...")


print("\nStarting webcam feed... Press ESC to stop and see summary.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Run YOLO detection
    results = model.track(frame,persist=True,conf=0.3,iou=0.5)[0]
    detections = sv.Detections.from_ultralytics(results)

    # Update tracker
    detections = tracker.update_with_detections(detections)

    # Record unique objects (by track_id)
    for det, class_id, track_id in zip(detections.xyxy, detections.class_id, detections.tracker_id):
        if track_id not in tracked_objects:
            tracked_objects.add(track_id)
            class_name = model.names[class_id]
            class_per_id[track_id] = class_name

    # Annotate the frame
    annotated_frame = bounding_box_annotator.annotate(scene=frame, detections=detections)
    annotated_image = label_annotator.annotate(scene=annotated_frame, detections=detections)

    # Show the live window
    cv2.imshow("YOLO Tracking", annotated_image)

    # Press ESC to quit
    if cv2.waitKey(q) == 27:
        print("Esc pressed. Ending detection...")
        break

cap.release()
cv2.destroyAllWindows()

# Summarize tracked results
if tracked_objects:
    
    counts = Counter(class_per_id.values())
    total = sum(counts.values())

    print("\n===== Detection Summary =====")
    print(f"Total unique objects detected: {total}")
    for cls, num in counts.items():
        print(f"{cls}: {num}")
else:
    print("No unique objects detected.")
