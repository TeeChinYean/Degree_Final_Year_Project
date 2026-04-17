import cv2
import asyncio
import multiprocessing as mp
from ultralytics import YOLO
from collections import Counter
import supervision as sv
import torch
import threading
from threading import Lock

import time
import serial
import json
import re

from flask import Flask, Response, request, jsonify
from flask_cors import CORS

import keyboard

# Global variables
data_list = []
data_lock = Lock()

# Shared event: camera capture runs always; YOLO inference / display / weight fusion follow this.
active_event = mp.Event()
active_event.clear()  # Inactive until camera page activates via web (or keyboard if wired)

# =========================
# Camera & YOLO Class
# =========================
# settings
model_path = r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\secondTrain\Extra_retrain2\weights\best.engine" if torch.cuda.is_available() else r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\secondTrain\Extra_retrain2\weights\best.onnx"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMG_SIZE = 640
BOX_SIZE = 480
class ItemDetect:
    def __init__(self, frame_q, yolo_q, display_q, active_event):
        self.frame_q = frame_q
        self.yolo_q = yolo_q
        self.display_q = display_q
        self.active_event = active_event
        self.model = YOLO(model_path, task="detect")
        
    def capture_process(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        print("📷 Camera capture running continuously")

        try:
            while True:
                success, frame = cap.read()
                if not success:
                    time.sleep(0.01)
                    continue

                if self.frame_q.full():
                    try:
                        self.frame_q.get_nowait()
                    except Exception:
                        pass

                self.frame_q.put(frame)
        finally:
            cap.release()

    def yolo_process(self):
            
            
            try:
                yolo_instance = self.model
                print("✅ Model loaded successfully")
            except Exception as e:
                print(f"❌ Failed to load model: {e}")
                return

            last_detect_time = time.time()
            avg_fps = 0

            while True:
                if not self.active_event.is_set():
                    time.sleep(0.05)
                    continue

                current_time = time.time()
                try:
                    frame = self.frame_q.get(timeout=0.1)
                except Exception:
                    continue

                if not self.active_event.is_set():
                    continue

                if frame is None:
                    continue

                h, w, _ = frame.shape
                x1, y1 = w//2 - BOX_SIZE//2, h//2 - BOX_SIZE//2
                x2, y2 = w//2 + BOX_SIZE//2, h//2 + BOX_SIZE//2

                time1 = time.time()
                
                results = yolo_instance.track(
                    frame, 
                    imgsz=IMG_SIZE,
                    conf=0.3,
                    iou=0.4,
                    persist=True,
                    half=True,
                    tracker="bytetrack.yaml",
                    verbose=False,
                    device=DEVICE
                )
                
                #fps
                time2 = time.time() 
                dt = time2 - time1
                if dt > 0:
                    curr_fps = 1.0 / dt
                    avg_fps = (avg_fps * 0.9 + curr_fps * 0.1) if avg_fps > 0 else curr_fps
                
                detections_found = False
                
                # 核心修正：安全检查结果和 ID
                if results and len(results[0].boxes) > 0 and results[0].boxes.id is not None:
                    det = sv.Detections.from_ultralytics(results[0])

                    for xyxy, cid, tid in zip(det.xyxy, det.class_id, det.tracker_id):
                        xc = (xyxy[0] + xyxy[2]) / 2
                        yc = (xyxy[1] + xyxy[3]) / 2

                        if x1 < xc < x2 and y1 < yc < y2:
                            detections_found = True
                            
                            label_name = yolo_instance.names[int(cid)]
                            
                            self.yolo_q.put({
                                "label": label_name,
                                "time": current_time
                            })
                            
                            cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (255, 0, 0), 2)
                            cv2.putText(frame, f"{label_name} ID:{int(tid)}", (int(xyxy[0]), int(xyxy[1]) - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

                # 绘制 UI 信息
                cv2.putText(frame, f"FPS: {avg_fps:.1f}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                # cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # 8. counting item appear time
                if detections_found:
                    last_detect_time = current_time

                # 9. Every processed frame goes to the web stream (not only when ROI has a hit)
                if self.display_q.full():
                    try:
                        self.display_q.get_nowait()
                        self.display_q.put(frame)
                    except Exception:
                        pass
                else:
                    self.display_q.put(frame)

# =========================
# Web App
# =========================
# settings
app = Flask(__name__)
CORS(app)
def flask_video_stream():
    global display_q, active_event
    
    while active_event.is_set():
        try:
            frame = display_q.get(timeout=0.1)
            
        except:
            continue
        
        
        if frame is None:
                time.sleep(0.1)
                continue
        #display frame in Flask(web)
        _, buffer = cv2.imencode('.jpg', frame)
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + buffer.tobytes()
            + b'\r\n'
        )
            
            
        



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
    # force=True ignores the Content-Type header if it's missing
    data = request.get_json(force=True, silent=True) 
    
    # Using 'is' for booleans is fine here, 
    # but ensure the frontend is sending actual booleans, not strings
    is_active = data.get("active") if data else None

    if is_active is True:
        active_event.set()
        print("🟢 Activated", flush=True)
        return jsonify({"status": "activated"}), 200
    elif is_active is False:
        active_event.clear()
        print("🔴 Deactivated", flush=True)
        return jsonify({"status": "deactivated"}), 200
    
    return jsonify({"error": "Invalid data", "received": data}), 400

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
# Weight Sensor //Finish, no issue and logic problem
# =========================
# settings
START_THRESHOLD = 0.4
END_THRESHOLD = 0.35
MIN_WEIGHT_DURATION = 0.3
MIN_YOLO_DURATION = 2.0

async def weight_worker(active_event, weight_q):
    
    weight_active = False
    weight_id = 0
    start_time = None
    buffer = ""
    ser = None

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

    try:
        while True:
            if not active_event.is_set():
                await asyncio.sleep(0.05)
                continue

            if ser.in_waiting:
                buffer += ser.read(ser.in_waiting).decode(errors="ignore")

                for line in buffer.splitlines():
                    m = re.search(r"-?\d+\.\d+|-?\d+", line)
                    if not m:
                        continue

                    weight = float(m.group())
                    now = time.time()

                    # === START DETECTION & RECORD===
                    if weight > START_THRESHOLD and not weight_active:
                        
                        temporary_list = []
                        weight_active = True
                        start_time = now
                        weight_id += 1

                        weight_q.put({"event": "start","weight_id": weight_id,"time": time.time(),"weight": weight })
                        temporary_list.append(weight)
                        print(f"🟢 START id={weight_id} | weight={weight:.2f}")

                    # ===KEEP ACTIVE STATE & RECORD TEMPORARY WEIGHTS===
                    elif weight_active and weight >= END_THRESHOLD:
                        temporary_list.append(weight)

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
                                "weight": avg_weight,
                            })

                            print(f"🔴 END   id={weight_id} | weight={avg_weight:.2f}")
                        else:
                            # Too short, reset but don't send end event 
                            weight_active = False

                buffer = ""

            await asyncio.sleep(0.02)

    finally:
        print("⚖️ Closing serial port")
        ser.close()


# =========================
# Parallel Main Controller
# =========================
async def main_item_detection(active_event, weight_q, yolo_q):
    session = None
    print("🧠 Main controller started")

    while True:
        if not active_event.is_set():
            session = None
            await asyncio.sleep(0.05)
            continue

        # 1. Process Weight Events
        while not weight_q.empty(): 
            w = weight_q.get()

            if w["event"] == "start":
                session = {
                    "weight_id": w["weight_id"],
                    "ws": w["time"],
                    "weight_start": w["weight"],
                    "we": None,
                    "weight_end": None,
                    "events": []
                }
            elif w["event"] == "end" and session and session["weight_id"] == w["weight_id"]:
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
    #s = session, e = event in session, label = yolo label in event
    labels = [e["label"] for e in s["events"]] 
    
    if not labels:
        print("❌ No YOLO detection during weight event")
        return

    item, freq = Counter(labels).most_common(1)[0] #most appear label
    duration = s["we"] - s["ws"]

    if duration < MIN_YOLO_DURATION:
        print(f"❌ Item detection too short ({duration:.2f}s)")
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


# =========================
# Main
# =========================
async def main():
    mp.set_start_method("spawn", force=True)
    
    global active_event, display_q
    
    display_q = mp.Queue(2)
    frame_q = mp.Queue(2)
    yolo_q = mp.Queue()
    weight_q = mp.Queue()

    # Item: Class
    item_detect = ItemDetect(frame_q, yolo_q, display_q, active_event)
    p_capture = mp.Process(target=item_detect.capture_process, args=())
    p_yolo    = mp.Process(target=item_detect.yolo_process, args=())
    p_capture.start()
    p_yolo.start()

    # ===== start async tasks =====
    task_weight = asyncio.create_task(weight_worker(active_event, weight_q))
    task_main   = asyncio.create_task(main_item_detection(active_event, weight_q, yolo_q))
    
    # Run Flask in a separate thread
    flask_thread = threading.Thread(target=lambda: run_flask(), daemon=True)
    flask_thread.start()
    
    try:
        await asyncio.gather(task_weight, task_main)
    finally:
        task_weight.cancel()
        task_main.cancel()
        print("🛑 Close joining processes...")
        active_event.clear() # Ensure processes know to stop
        
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
