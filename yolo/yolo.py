import multiprocessing
import queue
import time
import supervision as sv
from collections import Counter
import cv2
from ultralytics import YOLO
import torch
import os # Added for path manipulation clarity

# --- 1. Configuration and Constants ---
MODEL_NAMES = [
    r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\secondTrain\Extra_retrain2\weights\best.onnx",
    r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\firstTrain\retrain2\weights\best.onnx"
]
WEBCAM_SOURCE = 0 
MAX_QUEUE_SIZE = 10

def capture_frames(source, frame_queue, stop_event):
    
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Error: Cannot open video source {source}")
        return

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("Warning: Failed to read frame or stream ended.")
            break
        
        try:
            frame_queue.put(frame, timeout=0.005) 
        except queue.Full:
            pass 
        
        time.sleep(0.001) 

    cap.release()
    print("Frame capture stopped.")


# 3. Tracker Process Function (CPU Bound)
def run_tracker_in_process(model_name, frame_queue, stop_event, process_id, shared_class_per_id):

    try:
        model = YOLO(model_name, task='detect')
        print(f"Process {process_id}: Model {os.path.basename(model_name)} initialized.")
    except Exception as e:
        print(f"Process {process_id} failed to initialize model {model_name}: {e}")
        stop_event.set()
        return
    
    fps_start_time = time.time()

    while not stop_event.is_set():
        try:
            frame = frame_queue.get(timeout=1) 
            results = model.track(frame, persist=True, stream=False, verbose=False, conf=0.25, iou=0.45,tracker="botsort.yaml",device='cuda' if torch.cuda.is_available() else 'cpu' )
            
            fps_end_time = time.time()
            fps = 1 / (fps_end_time - fps_start_time) if (fps_end_time - fps_start_time) > 0 else 0
            fps_start_time = fps_end_time
            
            
            for r in results:
                im_bgr = r.plot() # Draws bounding boxes and track IDs
                detections = sv.Detections.from_ultralytics(r)
                
                if detections.tracker_id is not None:
                    for class_id, track_id in zip(
                        detections.class_id, detections.tracker_id
                    ):
                        if track_id is None:
                            continue  
                        
                        if track_id not in shared_class_per_id:
                            class_name = model.names[int(class_id)]
                            shared_class_per_id[track_id] = class_name


                fps_text = f"P{process_id} FPS: {fps:.2f}"
                cv2.putText(im_bgr, fps_text, (10, 30 + process_id * 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow(f"Process {process_id} - Model Output", im_bgr)


            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set() 

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Process {process_id} critical error: {e}")
            stop_event.set() 
            break

    print(f"Process {process_id} stopped.")


if __name__ == '__main__':
    
    # Initialization of ALL multiprocessing primitives MUST be inside this guard
    FRAME_QUEUE = multiprocessing.Queue(maxsize=MAX_QUEUE_SIZE)
    STOP_EVENT = multiprocessing.Event()
    
    # Use Manager context manager for clean shutdown of shared data proxies
    with multiprocessing.Manager() as manager:
        
        # Shared dictionary proxy (ID -> Class Name)
        SHARED_CLASS_PER_ID = manager.dict() 
        # Note: We can omit SHARED_TRACKED_OBJECTS (list) as the dictionary keys track uniqueness
        
        # Start the frame capture process (I/O)
        capture_thread = multiprocessing.Process(target=capture_frames, args=(WEBCAM_SOURCE, FRAME_QUEUE, STOP_EVENT))
        capture_thread.start()
        print("Frame capture process started.")

        # Start the tracker processes (CPU)
        tracker_processes = []
        for i, model_name in enumerate(MODEL_NAMES):
            process = multiprocessing.Process(target=run_tracker_in_process, args=(model_name, FRAME_QUEUE, STOP_EVENT, i, SHARED_CLASS_PER_ID))
            tracker_processes.append(process)
            process.start()

        try:
            for process in tracker_processes:
                process.join()
                
        except KeyboardInterrupt:
            print("\nReceived KeyboardInterrupt. Stopping processes...")

        finally:
            STOP_EVENT.set() 
            capture_thread.join(timeout=2)
            cv2.destroyAllWindows()
            

            if SHARED_CLASS_PER_ID:
                print("\nSummary of unique tracked objects:")
                class_counts = Counter(SHARED_CLASS_PER_ID.values())
                for class_name, count in class_counts.items():
                    print(f"| {class_name:<10}: {count}")
            else:
                print("\nNo Item Detect.")
                
            print("Application closed gracefully.")
            exit(0)
