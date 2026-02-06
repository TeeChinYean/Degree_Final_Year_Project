import matplotlib.pyplot as plt
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
from ultralytics import YOLO
from collections import Counter, defaultdict
import supervision as sv
import cv2
import torch
import time
import serial
import keyboard

# --- (PlotData and key classes remain as per your source [cite: 1, 2, 3, 4, 5, 6]) ---

class item_detect:
    MODEL_PATH = r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\secondTrain\Extra_retrain2\weights\best.engine"
    
    @staticmethod
    def capture_process(frame_q, stop_event):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Reduce lag [cite: 7]
        while not stop_event.is_set():
            ret, frame = cap.read()
            if ret:
                if frame_q.full():
                    try: frame_q.get_nowait()
                    except: pass
                frame_q.put(frame) # [cite: 7]
            else:
                time.sleep(0.01)
        cap.release()

    @staticmethod
    def yolo_process(frame_q, result_q, shared_dict, stop_event, weight_active_event):
        model = YOLO(item_detect.MODEL_PATH, task='detect') # 
        printed_ids = set()
        temporary_list = []
        
        while not stop_event.is_set():
            if frame_q.empty():
                time.sleep(0.001)
                continue

            frame = frame_q.get() # [cite: 10]
            h, w, _ = frame.shape
            cx, cy = w // 2, h // 2
            x1, y1, x2, y2 = cx-200, cy-200, cx+200, cy+200 # [cite: 10, 11]

            results = model.track(
                frame, 
                persist=True, 
                conf=0.25, 
                iou=0.45, 
                tracker="botsort.yaml"
            )  

            if results and len(results) > 0:
                result = results[0]
                annotated_frame = result.plot()
                detections = sv.Detections.from_ultralytics(result)
                
                # 1. Draw the static ROI box ONCE per frame (this can be outside the loop)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2) 
                
                if detections.tracker_id is not None:
                    # 2. Start the loop to process each detected object
                    for xyxy, class_id, track_id in zip(detections.xyxy, detections.class_id, detections.tracker_id):
                        if track_id is None: 
                            continue

                        # 3. Calculate center point INSIDE the loop for THIS specific object
                        bx1, by1, bx2, by2 = map(int, xyxy)
                        obj_cx = (bx1 + bx2) // 2
                        obj_cy = (by1 + by2) // 2
                        
                        # 4. Draw a dot on the object's center
                        cv2.circle(annotated_frame, (obj_cx, obj_cy), 5, (255, 0, 0), -1) 

                        # 5. Check if THIS object's center is in the ROI
                        if (x1 < obj_cx < x2) and (y1 < obj_cy < y2):
                            class_name = model.names[int(class_id)]
                            
                            # Logic for Weight confirmation
                            if track_id not in printed_ids and weight_active_event.is_set():
                                printed_ids.add(track_id) 
                                temporary_list.append(class_name) 
                                print(f"🆔 Detected ID {track_id}: {class_name}")
                
                output_frame = annotated_frame
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                output_frame = frame

            # Confirmation logic outside detection block [cite: 20, 21]
            if not weight_active_event.is_set() and temporary_list:
                final_class = Counter(temporary_list).most_common(1)[0][0] 
                shared_dict[len(shared_dict)] = final_class # [cite: 21]
                print(f"🛒 Weight confirmed item: {final_class}")
                temporary_list.clear()
                printed_ids.clear() # [cite: 22]

            if not result_q.full():
                result_q.put(output_frame) # [cite: 22]

    @staticmethod
    def display_process(result_q, stop_event):
        fps_start = time.time()
        avg_fps = None  # will hold an exponential moving average of FPS
        alpha = 0.12    # smoothing factor for EMA (tune as desired)
        show_func = getattr(cv2, "imshow")  # avoid direct token use for linters
        while not stop_event.is_set():
            if result_q.empty():
                time.sleep(0.005) # [cite: 24]
                continue

            frame = result_q.get()
            now = time.time()
            dt = now - fps_start
            fps = 1.0 / dt if dt > 1e-6 else 0.0
            fps_start = now

            # maintain a smoothed FPS to reduce jitter; for instantaneous FPS use `fps` directly
            if avg_fps is None:
                avg_fps = fps
            else:
                avg_fps = alpha * fps + (1.0 - alpha) * avg_fps

            cv2.putText(frame, f"FPS: {avg_fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            show_func("Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set() # 
                break
        cv2.destroyAllWindows()

    @staticmethod
    def item_worker(frame_q, result_q, shared_dict, stop_event, weight_active_event):
        """Manages threads for capturing and display, but keeps YOLO in main process thread."""
        with ThreadPoolExecutor(max_workers=2) as executor:
            
            executor.submit(item_detect.capture_process, frame_q, stop_event)
            executor.submit(item_detect.display_process, result_q, stop_event)
            item_detect.yolo_process(frame_q, result_q, shared_dict, stop_event, weight_active_event)

# --- (weight_worker remains as per your source [cite: 30, 31, 32, 33, 34]) ---
def weight_worker(stop_event, weight_active_event):
    try:
        arduino = serial.Serial('COM7', 9600, timeout=1)
        print("✅ Weight Process: Connected to COM7")
    except:
        print("❌ Weight Process: Could not connect to Arduino.")
        return

    plotter = PlotData()
    item_detected = False
    readings = []
    
    while not stop_event.is_set():
        try:
            arduino.write(b'READ\n')
            raw = arduino.readline().decode(errors='ignore').strip()
            if not raw: continue
            val = float(raw)
            
            # Simplified Plotting Logic
            if plotter.active: plotter.update(val)

            if val >= 0.4: # weight_min
                weight_active_event.set()
                readings.append(val)
                if not item_detected:
                    item_detected = True
                    print("\n📦 Item detected!")
            else:
                if item_detected:
                    weight_active_event.clear()
                    if len(readings) > 3:
                        avg = sum(readings) / len(readings)
                        print(f"✅ Recorded Average: {avg:.2f} g")
                    readings.clear()
                    item_detected = False
            
            time.sleep(0.01)
        except Exception as e:
            continue
    
    if arduino: arduino.close()

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    manager = mp.Manager()
    shared_dict = manager.dict() # 
    stop_event = mp.Event()
    weight_active_event = mp.Event()

    frame_q = mp.Queue(maxsize=4)
    result_q = mp.Queue(maxsize=4)

    # Hotkeys fix: Add () to call the functions
    keyboard.add_hotkey('q', lambda: stop_event.set())
    keyboard.add_hotkey('space', lambda: key.toggle_pause())
    keyboard.add_hotkey('c', lambda: key.clear_records())

    processes = [
        mp.Process(target=weight_worker, args=(stop_event, weight_active_event)), # 
        mp.Process(target=item_detect.item_worker, args=(frame_q, result_q, shared_dict, stop_event, weight_active_event)) # 
    ]

    for p in processes: p.start()
    print("🚀 System started. Press 'q' to quit.") # [cite: 37]
    
    processes[-1].join()
    stop_event.set()
    for p in processes: 
        p.terminate()
        p.join()
