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

from flask import Flask, Response
from flask_cors import CORS
import threading
from threading import Lock
import keyboard
import requests
active_event = mp.Event()
active_event.set()
# =========================
# 参数配置
# =========================
MODEL_PATH = r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\secondTrain\Extra_retrain2\weights\best.onnx"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")
IMG_SIZE = 640
BOX_SIZE = 400

START_THRESHOLD = 0.4
END_THRESHOLD = 0.35
MIN_WEIGHT_DURATION = 0.3
MIN_YOLO_DURATION = 2.5

display_q = None
stop_event = None

app = Flask(__name__)
CORS(app)
data_list = []
data_lock = Lock()
# =========================
# Camera
# =========================

def capture_process(frame_q, stop_event):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("📷 Camera started")

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        if frame_q.full():
            frame_q.get(timeout=0.1)

        frame_q.put_nowait(frame)

    cap.release()


def yolo_process(frame_q, yolo_q, display_q, stop_event):
    model = None
    print("YOLO process started")

    while not stop_event.is_set():
        if not active_event.is_set():
            time.sleep(0.2)
            continue

        if model is None:
            model = YOLO(MODEL_PATH, task="detect")
            
        try:
            frame = frame_q.get(timeout=0.1)
        except:
            continue

        h, w, _ = frame.shape
        x1, y1 = w//2 - BOX_SIZE//2, h//2 - BOX_SIZE//2
        x2, y2 = w//2 + BOX_SIZE//2, h//2 + BOX_SIZE//2

        results = model.track(
            frame,
            imgsz=IMG_SIZE,
            conf=0.3,
            iou=0.4,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False,
            device = DEVICE
        )

        now = time.time()

        if results and results[0].boxes.id is not None:
            det = sv.Detections.from_ultralytics(results[0])

            for xyxy, cid, tid in zip(det.xyxy, det.class_id, det.tracker_id):
                xc = (xyxy[0] + xyxy[2]) / 2
                yc = (xyxy[1] + xyxy[3]) / 2

                if x1 < xc < x2 and y1 < yc < y2:
                    yolo_q.put({
                        "label": model.names[int(cid)],
                        "time": now
                    })

                    cv2.putText(
                        frame,
                        f"{model.names[int(cid)]}", (int(xyxy[0]), int(xyxy[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2
                    )

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        if not display_q.full():
            display_q.put(frame)


# =========================
# Display
# =========================
# def display_process(display_q, stop_event):
#     fps_last = time.time()
#     fps = 0

#     while not stop_event.is_set():
#         try:
#             frame = display_q.get(timeout=0.1)
#         except:
#             continue

#         now = time.time()
#         dt = now - fps_last
#         fps_last = now

#         if dt > 0:
#             fps = 0.9 * fps + 0.1 * (1 / dt)

#         cv2.putText(frame, f"FPS: {fps:.2f}",
#                     (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
#                     1, (0, 255, 0), 2)

#         cv2.imshow("Smart Checkout System", frame)

#         if cv2.waitKey(1) & 0xFF == ord("q"):
#             stop_event.set()
#             break

#     cv2.destroyAllWindows()

def flask_video_stream():
    global display_q, stop_event
    fps_last = time.time()
    fps = 0
    while not stop_event.is_set():
        try:
            frame = display_q.get(timeout=0.1)
        except:
            continue
        
        now = time.time()
        dt = now - fps_last
        fps_last = now

        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1 / dt)

        cv2.putText(frame, f"FPS: {fps:.2f}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2)

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

def run_flask():
    app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)

def data_stream():
    last_sent = None

    while True:
        with data_lock:
            if not data_list:
                time.sleep(0.05)
                continue
            latest = data_list[-1]  # 只取最后一条
            payload = json.dumps(latest, ensure_ascii=False)

        if payload != last_sent:
            last_sent = payload
            yield f"data: {payload}\n\n"

        time.sleep(0.2)

# =========================
# Weight Sensor
# =========================
async def weight_worker(stop_event, weight_q):
    ser = None
    for port in ("COM7", "COM6", "COM5", "COM4", "COM3"):#the main port put at the first, it not then try other
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
            # 🔴 HARD EXIT CHECK (this is the key)
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

                    if weight > START_THRESHOLD and not weight_active:
                        temporary_list = []
                        weight_active = True
                        start_time = now
                        weight_id += 1

                        weight_q.put({
                            "event": "start",
                            "weight_id": 20,
                            "time": time.time(),
                            "weight": 20
                        })

                        temporary_list.append(weight)
                        print(f"🟢 START id={weight_id} | weight={weight:.2f}")

                    elif weight_active and weight >= END_THRESHOLD:
                        # 🟡 ACTIVE STATE — keep collecting
                        temporary_list.append(weight)
                        print(f"Id = {weight_id} | weight = {weight:.2f}")

                    elif weight < END_THRESHOLD and weight_active:
                        if now - start_time >= MIN_WEIGHT_DURATION:
                            weight_active = False

                            temporary_weight = (
                                temporary_list[1:-1]# remove when begin data and end data for accurate
                                # if len(temporary_list) > 3
                                # else temporary_list
                                #forgot what function it is 
                            )

                            avg_weight = sum(temporary_weight) / len(temporary_weight)

                            weight_q.put({
                                "event": "end",
                                "weight_id": weight_id,
                                "time": now,
                                "weight": avg_weight
                            })

                            print(f"🔴 END   id={weight_id} | weight={avg_weight:.2f}")

                buffer = ""

            await asyncio.sleep(0.02)

    finally:
        print("⚖️ Closing serial port")
        ser.close()



# =========================
# Main Controller
# =========================
async def main_item_detection(stop_event, weight_q, yolo_q):
    session = None
    print("🧠 Main controller started")

    while not stop_event.is_set():
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
                session["we"] = w["time"]
                session["weight_end"] = w["weight"]
                process_session(session)
                
                session = None


        while not yolo_q.empty():
            y = yolo_q.get()
            if session and y["time"] >= session["ws"]:
                session["events"].append(y)

        await asyncio.sleep(0.02)

data_list = []
def process_session(s):
    global data_list
    labels = [e["label"] for e in s["events"]]
    if not labels:
        print("❌ No YOLO detection")
        return

    item, freq = Counter(labels).most_common(1)[0] # counter appear most one
    duration = s["we"] - s["ws"] # end - start time

    if duration < MIN_YOLO_DURATION:
        print("❌ YOLO too short")
        return

    # 使用结束重量
    final_weight = s["weight_end"]
    
    print("\n✅ FINAL RESULT")
    print(f"Item      : {item}")
    print(f"Weight    : {final_weight:.2f} g")
    print(f"Duration  : {duration:.2f}s\n")
    
    
    #store to json
    new_data = {
            "item": item,
            "weight": f"{final_weight:.2f}",
        }
    
    # old one, store the data in file
    #------------------------------------
    # file_path = 'data.json'
    # data_list.append(new_data)
    # with open(file_path, 'w', encoding='utf-8') as f:
    #     json.dump(data_list, f, indent=4) 
    
    # send data to webpage
    url = "http://localhost/greenpoint_site/Front-end/camera.php"
    r = requests.post(url, json=new_data,timeout=5)
    print(f"✅ Successfully inserted: {item}")


# =========================
# Entry
# =========================
async def main():
    #data file setup
    # file_path = 'data.json'
    # if os.path.exists(file_path):
    #     try:
    #         with open(file_path, 'w', encoding='utf-8') as f: # clean old data
    #             json.dump([], f)
    #             print(f"✅ Ready: {file_path} has been reset/created.")
    #     except Exception as e:
    #         print(f"❌ Error resetting {file_path}: {e}")
            
    mp.set_start_method("spawn", force=True)# keep for Prevents accidental fallback

    #queues & events setup
    global stop_event
    global display_q
    stop_event = mp.Event()

    
    display_q = mp.Queue(2)
    frame_q = mp.Queue(2)
    yolo_q = mp.Queue()
    weight_q = mp.Queue()

    # ===== start processes =====
    p_capture = mp.Process(target=capture_process, args=(frame_q, stop_event))
    p_yolo    = mp.Process(target=yolo_process, args=(frame_q, yolo_q, display_q, stop_event))
    # p_display = mp.Process(target=display_process, args=(display_q, stop_event))

    p_capture.start()
    p_yolo.start()
    # p_display.start()
    
    # ===== start async tasks =====
    task_weight = asyncio.create_task(weight_worker(stop_event, weight_q))
    task_main   = asyncio.create_task(main_item_detection(stop_event, weight_q, yolo_q))

    threading.Thread(
        #use threading run web
        target=lambda: app.run(
            host='0.0.0.0',
            port=5000,
            threaded=True,
            use_reloader=False
        ),
        daemon=True
    ).start()
    
    try:
        await asyncio.gather(task_weight, task_main)
    finally:
        # Cancel any still-running async tasks
        task_weight.cancel()
        task_main.cancel()

        # ===== join & terminate processes =====
        print("🛑 Joining processes...")
        for p in (p_capture, p_yolo): #, p_display
            if p.is_alive():
                p.join(timeout=1)
                if p.is_alive():
                    p.terminate()# double check to stop process
        print("✅ All processes stopped")



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⏹ Stopped")
