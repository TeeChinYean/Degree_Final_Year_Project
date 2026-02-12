import cv2
import time
import serial
import asyncio
import multiprocessing as mp
from ultralytics import YOLO
from collections import Counter
import supervision as sv
import torch
import json
import re
import os
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import threading
from threading import Lock
import keyboard
import requests

# =========================
# Settings
# =========================
# Model settings
MODEL_PATH = r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\secondTrain\Extra_retrain2\weights\best.onnx"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

IMG_SIZE = 640
BOX_SIZE = 480

# Weight sensor settings
START_THRESHOLD = 0.4
END_THRESHOLD = 0.35
MIN_WEIGHT_DURATION = 0.3
MIN_YOLO_DURATION = 2.5
NO_DETECT_SLEEP_TIME = 45.0  # Time before camera sleeps if no YOLO detection

# Global variables
stop_event = None
data_list = []
data_lock = Lock()

# Shared event to control system state (Active/Inactive)
active_event = mp.Event()
active_event.set()  # Default to active initially

# Webapp settings
app = Flask(__name__)
CORS(app)

# =========================
# Camera & YOLO Class
# =========================
class ItemDetect:
    def __init__(self, frame_q, stop_event, yolo_q, display_q, active_event):
        self.frame_q = frame_q
        self.stop_event = stop_event
        self.yolo_q = yolo_q
        self.display_q = display_q
        self.active_event = active_event
        self.sleeping = False
        
    def capture_process(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        print("📷 Camera started")

        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            # If queue full, drop oldest frame to reduce latency
            if self.frame_q.full():
                try:
                    self.frame_q.get_nowait()
                except:
                    pass

            self.frame_q.put(frame)
            
        cap.release()

    def yolo_process(self):
        model = None
        print("🚀 YOLO process started")
        last_detect_time = time.time()
        
        while not self.stop_event.is_set():
            # 1. System Active Check
            if not self.active_event.is_set():
                # If we are here, the system is PAUSED (Standby).
                # We simply wait for the Weight Sensor or Web Button to wake us.
                self.sleeping = True 
                time.sleep(0.2)
                continue

            # 2. Wake-up Logic (Transition from Sleep to Active)
            if self.sleeping:
                print("🔁 Waking up (System Activated)")
                self.sleeping = False
                last_detect_time = time.time() # Reset timer immediately on wake

            # Load model lazily
            if model is None:
                model = YOLO(MODEL_PATH, task="detect")
                
            try:
                frame = self.frame_q.get(timeout=0.1)
            except:
                continue

            h, w, _ = frame.shape
            x1, y1 = w//2 - BOX_SIZE//2, h//2 - BOX_SIZE//2
            x2, y2 = w//2 + BOX_SIZE//2, h//2 + BOX_SIZE//2

            # 3. Run Tracking
            results = model.track(
                frame,
                imgsz=IMG_SIZE,
                conf=0.3,
                iou=0.4,
                persist=True,
                tracker="bytetrack.yaml",
                verbose=False,
                device=DEVICE
            )

            now = time.time()
            detections_found = False

            if results and results[0].boxes.id is not None:
                det = sv.Detections.from_ultralytics(results[0])

                for xyxy, cid, tid in zip(det.xyxy, det.class_id, det.tracker_id):
                    xc = (xyxy[0] + xyxy[2]) / 2
                    yc = (xyxy[1] + xyxy[3]) / 2

                    if x1 < xc < x2 and y1 < yc < y2:
                        detections_found = True
                        self.yolo_q.put({
                            "label": model.names[int(cid)],
                            "time": now
                        })

                        cv2.putText(
                            frame,
                            f"{model.names[int(cid)]}", 
                            (int(xyxy[0]), int(xyxy[1]) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2
                        )

            # 4. Timeout Logic
            if detections_found:
                last_detect_time = now # Reset timer if we see something
            
            # # Check for timeout
            # if (now - last_detect_time >= NO_DETECT_SLEEP_TIME):
            #     print(f"😴 No detection for {NO_DETECT_SLEEP_TIME}s → Deactivating system")
            #     self.sleeping = True
            #     self.active_event.clear() # <--- THIS IS THE KEY FIX
            #     # Clearing this forces the loop to go back to Step 1 and wait
                
            #     # Clear the display queue so the screen goes black/stops updating
            #     while not self.display_q.empty():
            #         try: self.display_q.get_nowait()
            #         except: pass
            #     self.display_q.put(None) 

            # 5. Display Logic (Only if active)
            if not self.sleeping:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                if not self.display_q.full():
                    self.display_q.put(frame)

# =========================
# Web App
# =========================
def flask_video_stream():
    global display_q, stop_event
    fps_last = time.time()
    fps = 0
    
    while not stop_event.is_set():
        try:
            frame = display_q.get(timeout=0.1)
        except:
            continue
        
        # Handle sleep state (None frame)
        if frame is None:
            time.sleep(0.1)
            continue

        # now = time.time()
        # dt = now - fps_last
        # fps_last = now

        # if dt > 0:
        #     fps = 0.9 * fps + 0.1 * (1 / dt)

        # cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + buffer.tobytes()
            + b'\r\n'
        )
        
        if keyboard.is_pressed('q'):
            stop_event.set()
            break

@app.route('/video')
def video():
    return Response(
        flask_video_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/word_event')
def word_event():
    return Response(
        data_stream(),
        mimetype='text/event-stream',
        headers={
            "Cache-Control": "no-store",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.route("/history")
def get_history():
    with data_lock:
        return jsonify(data_list)

@app.route("/clear_data", methods=["POST"])
def clear_data():
    global data_list
    with data_lock:
        data_list.clear()
    print("🗑 Data cleared by user action")
    return jsonify({"status": "cleared"})


@app.route("/activate", methods=["POST"])
def activate():
    data = request.get_json()
    if data and data.get("active"):
        active_event.set()
        print("🟢 System activated via web")
    else:
        active_event.clear()
        print("🔴 System de-activated via web")
    return jsonify({"status": "ok"})

def run_flask():
    app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)

def data_stream():
    last_index = 0

    while True:
        new_item = None

        with data_lock:
            if last_index < len(data_list):
                new_item = data_list[last_index]
                last_index += 1

        if new_item:
            payload = json.dumps(new_item, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        else:
            yield ": keep-alive\n\n"

        time.sleep(0.2)



# =========================
# Weight Sensor
# =========================
async def weight_worker(stop_event, weight_q, active_event):
    ser = None
    # Try connecting to ports
    for port in ("COM7", "COM6", "COM5", "COM4", "COM3"):
        try:
            ser = serial.Serial(port, 9600, timeout=0.1)
            ser.write(b'\n')
            ser.reset_input_buffer()
            print(f"⚖️ Weight sensor connected on {port}")
            break
        except:
            pass

    if not ser:
        print("❌ Weight sensor not found")
        return

    weight_active = False
    weight_id = 0
    start_time = None
    buffer = ""

    try:
        while True:
            if stop_event.is_set():
                print("⚖️ Weight worker stopping")
                break

            if ser.in_waiting:
                buffer += ser.read(ser.in_waiting).decode(errors="ignore")

                for line in buffer.splitlines():
                    m = re.search(r"-?\d+\.\d+|-?\d+", line)
                    if not m:
                        continue

                    weight = float(m.group())
                    now = time.time()

                    # === START DETECTION ===
                    if weight > START_THRESHOLD and not weight_active:
                        # 🟢 WAKE ON WEIGHT LOGIC
                        if not active_event.is_set():
                            print(f"⚖️ Weight detected ({weight:.2f}g) -> 🟢 AUTO-ACTIVATING SYSTEM")
                            active_event.set()

                        temporary_list = []
                        weight_active = True
                        start_time = now
                        weight_id += 1

                        # FIXED: Used dynamic weight_id and actual weight instead of hardcoded 20
                        weight_q.put({
                            "event": "start",
                            "weight_id": weight_id,
                            "time": time.time(),
                            "weight": weight 
                        })

                        temporary_list.append(weight)
                        print(f"🟢 START id={weight_id} | weight={weight:.2f}")

                    # === ACTIVE STATE ===
                    elif weight_active and weight >= END_THRESHOLD:
                        temporary_list.append(weight)
                        # Optional: Print less frequently to avoid spam
                        # print(f"Id = {weight_id} | weight = {weight:.2f}")

                    # === END DETECTION ===
                    elif weight < END_THRESHOLD and weight_active:
                        if now - start_time >= MIN_WEIGHT_DURATION:
                            weight_active = False

                            # Removing edges for accuracy
                            temporary_weight = temporary_list[1:-1]
                            
                            # FIXED: Prevent division by zero if list is empty
                            if len(temporary_weight) > 0:
                                avg_weight = sum(temporary_weight) / len(temporary_weight)
                            else:
                                avg_weight = sum(temporary_list) / len(temporary_list) if temporary_list else 0

                            weight_q.put({
                                "event": "end",
                                "weight_id": weight_id,
                                "time": now,
                                "weight": avg_weight
                            })

                            print(f"🔴 END   id={weight_id} | weight={avg_weight:.2f}")
                        else:
                            # Too short, reset but don't send end event (or handle as false positive)
                            weight_active = False

                buffer = ""

            await asyncio.sleep(0.02)

    finally:
        print("⚖️ Closing serial port")
        ser.close()


# =========================
# Mixed Controller
# =========================
async def main_item_detection(stop_event, weight_q, yolo_q):
    session = None
    print("🧠 Main controller started")

    while not stop_event.is_set():
        # 1. Process Weight Events
        while not weight_q.empty(): 
            w = weight_q.get()

            if w["event"] == "start":
                session = {
                    "weight_id": w["weight_id"],
                    "ws": w["time"],
                    "we": None,
                    "weight_start": w["weight"],
                    "weight_end": None,
                    "events": []
                }

            elif w["event"] == "end" and session:
                # Ensure we match the correct weight ID if overlapped (basic check)
                if session["weight_id"] == w["weight_id"]:
                    session["we"] = w["time"]
                    session["weight_end"] = w["weight"]
                    process_session(session)
                    session = None

        # 2. Process YOLO Events
        while not yolo_q.empty():
            y = yolo_q.get()
            # Only add if we have an active session and detection is after start
            if session and y["time"] >= session["ws"]:
                session["events"].append(y)

        await asyncio.sleep(0.02)


# =========================
# Process Session
# =========================
def process_session(s):
    global data_list
    labels = [e["label"] for e in s["events"]]
    
    if not labels:
        print("❌ No YOLO detection during weight event")
        return

    item, freq = Counter(labels).most_common(1)[0]
    duration = s["we"] - s["ws"]

    if duration < MIN_YOLO_DURATION:
        print(f"❌ YOLO too short ({duration:.2f}s)")
        return

    final_weight = s["weight_end"]
    print("\n✅ FINAL RESULT")
    print(f"Item      : {item}")
    print(f"Weight    : {final_weight:.2f} g")
    print(f"Duration  : {duration:.2f}s\n")
    
    new_data = {
        "item": item,
        "weight": f"{final_weight:.2f}",
    }
    # Store locally for EventStream
    with data_lock:
        data_list.append(new_data)
        if len(data_list) > 20:
            data_list.pop(0)

    # Send to PHP backend
    try:
        url = "http://localhost/greenpoint_site/Front-end/camera.php"
        requests.post(url, json=data_list, timeout=5)
        print(f"✅ Successfully inserted to DB: {item}")
    except Exception as e:
        print(f"⚠️ Failed to post to PHP: {e}")


# =========================
# Entry
# =========================
async def main():
    mp.set_start_method("spawn", force=True)
    
    global stop_event, display_q
    
    stop_event = mp.Event()
    display_q = mp.Queue(2)
    frame_q = mp.Queue(2)
    yolo_q = mp.Queue()
    weight_q = mp.Queue()

    # active_event is global
    item_detect = ItemDetect(frame_q, stop_event, yolo_q, display_q, active_event)
    
    # ===== start processes =====
    p_capture = mp.Process(target=item_detect.capture_process, args=())
    p_yolo    = mp.Process(target=item_detect.yolo_process, args=())
    p_capture.start()
    p_yolo.start()

    # ===== start async tasks =====
    # Note: Passed active_event to weight_worker
    task_weight = asyncio.create_task(weight_worker(stop_event, weight_q, active_event))
    task_main   = asyncio.create_task(main_item_detection(stop_event, weight_q, yolo_q))
    
    # Run Flask in a separate thread
    flask_thread = threading.Thread(target=lambda: run_flask(), daemon=True)
    flask_thread.start()
    
    try:
        await asyncio.gather(task_weight, task_main)
    finally:
        # Cleanup
        task_weight.cancel()
        task_main.cancel()

        print("🛑 Joining processes...")
        stop_event.set() # Ensure processes know to stop
        
        for p in (p_capture, p_yolo): 
            if p.is_alive():
                p.join(timeout=1)
                if p.is_alive():
                    p.terminate()
        print("✅ All processes stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⏹ Stopped by User")
