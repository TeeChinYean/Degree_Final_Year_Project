import multiprocessing
import queue
import time
import supervision as sv
from collections import defaultdict, Counter
import cv2
from ultralytics import YOLO


MODEL_NAMES = [r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\secondTrain\Extra_retrain2\weights\best.pt",
            r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\firstTrain\retrain2\weights\best.pt"]
WEBCAM_SOURCE = 0 


FRAME_QUEUE = multiprocessing.Queue(maxsize=10)
STOP_EVENT = multiprocessing.Event()


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
def run_tracker_in_process(model_name, frame_queue, stop_event, process_id):
    model = YOLO(model_name, task='detect')
    print(f"Process {process_id}: Model {model_name.split(r'\\')[-1]} initialized.")
    fps_start_time = time.time()

    while not stop_event.is_set():
        try:
            frame = frame_queue.get(timeout=1) 
            results = model.predict(frame, stream=False, verbose=False, conf=0.25, iou=0.45)
            
            fps_end_time = time.time()
            fps = 1 / (fps_end_time - fps_start_time)
            fps_start_time = fps_end_time
            fps_text = f"FPS: {fps:.2f}"
            cv2.putText(frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            for r in results:
                im_bgr = r.plot() 
                cv2.imshow(f"Process {process_id} - Model Output", im_bgr)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set() 

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Process {process_id} error: {e}")
            break

    print(f"Process {process_id} stopped.")


if __name__ == '__main__':
    
    capture_thread = multiprocessing.Process(
        target=capture_frames, 
        args=(WEBCAM_SOURCE, FRAME_QUEUE, STOP_EVENT)
    )
    capture_thread.start()
    print("Frame capture process started.")

    tracker_processes = []
    for i, model_name in enumerate(MODEL_NAMES):
        process = multiprocessing.Process(
            target=run_tracker_in_process, 
            args=(model_name, FRAME_QUEUE, STOP_EVENT, i)
        )
        tracker_processes.append(process)
        process.start()

    try:
        for process in tracker_processes:
            process.join()
            
    except KeyboardInterrupt:
        pass

    finally:
        #cleanup
        STOP_EVENT.set() 
        capture_thread.join(timeout=2)
        cv2.destroyAllWindows()
        print("Application closed gracefully.")
        exit(0)
