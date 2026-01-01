import cv2
import time
import serial
import asyncio
import multiprocessing as mp
from ultralytics import YOLO
from collections import Counter
import supervision as sv
import json


# =========================
# 参数配置
# =========================
MODEL_PATH = r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\secondTrain\Extra_retrain2\weights\best.engine"
IMG_SIZE = 640
BOX_SIZE = 400

START_THRESHOLD = 0.4
END_THRESHOLD = 0.35
MIN_WEIGHT_DURATION = 0.3
MIN_YOLO_DURATION = 2.5


# =========================
# Camera
# =========================
def capture_process(frame_q, stop_event):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("📷 Camera started")

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        if frame_q.full():
            frame_q.get_nowait()

        frame_q.put_nowait(frame)

    cap.release()


# =========================
# YOLO
# =========================
def yolo_process(frame_q, yolo_q, display_q, stop_event):
    model = YOLO(MODEL_PATH, task="detect")
    print("🤖 YOLO process started")

    while not stop_event.is_set():
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
            verbose=False
        )

        now = time.time()

        if results and results[0].boxes.id is not None:
            det = sv.Detections.from_ultralytics(results[0])

            for xyxy, cid, tid in zip(det.xyxy, det.class_id, det.tracker_id):
                xc = (xyxy[0] + xyxy[2]) / 2
                yc = (xyxy[1] + xyxy[3]) / 2

                if x1 < xc < x2 and y1 < yc < y2:
                    yolo_q.put({
                        "tracker_id": int(tid),
                        "label": model.names[int(cid)],
                        "time": now
                    })

                    cv2.putText(
                        frame,
                        f"{model.names[int(cid)]} ID:{int(tid)}",
                        (int(xyxy[0]), int(xyxy[1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (255, 0, 0), 2
                    )

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        if not display_q.full():
            display_q.put(frame)


# =========================
# Display
# =========================
def display_process(display_q, stop_event):
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

        cv2.imshow("Smart Checkout System", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            stop_event.set()
            break

    cv2.destroyAllWindows()


# =========================
# Weight Sensor
# =========================
async def weight_worker(stop_event, weight_q):
    ser = None
    for port in ("COM7", "COM6", "COM5", "COM4", "COM3"):
        try:
            ser = serial.Serial(port, 9600, timeout=0.1)
            time.sleep(2)
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
                            "weight_id": weight_id,
                            "time": now,
                            "weight": weight
                        })

                        temporary_list.append(weight)
                        print(f"🟢 START id={weight_id} | weight={weight:.2f}")

                    elif weight_active and weight >= END_THRESHOLD:
                        # 🟡 ACTIVE STATE — keep collecting
                        temporary_list.append(weight)

                    elif weight < END_THRESHOLD and weight_active:
                        if now - start_time >= MIN_WEIGHT_DURATION:
                            weight_active = False

                            temporary_weight = (
                                temporary_list[1:-1]
                                if len(temporary_list) > 3
                                else temporary_list
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
                session["weight_end"] = w["weight"]  # 保存结束重量
                process_session(session)
                
                session = None


        while not yolo_q.empty():
            y = yolo_q.get()
            if session and y["time"] >= session["ws"]:
                session["events"].append(y)

        await asyncio.sleep(0.02)


def process_session(s):
    labels = [e["label"] for e in s["events"]]
    if not labels:
        print("❌ No YOLO detection")
        return

    item, freq = Counter(labels).most_common(1)[0]
    duration = s["we"] - s["ws"]

    if duration < MIN_YOLO_DURATION:
        print("❌ YOLO too short")
        return

    # 使用结束重量
    final_weight = s["weight_end"]

    print("\n✅ FINAL RESULT")
    print(f"Weight ID : {s['weight_id']}")
    print(f"Item      : {item}")
    print(f"Weight    : {final_weight:.2f} g")
    print(f"Duration  : {duration:.2f}s\n")
    with open('data.json', 'a', encoding='utf-8') as f:
        json.dump({
            "weight_id": s['weight_id'],
            "item": item,
            "weight": final_weight,
            "duration": duration
        }, f, indent=4)
        f.write('\n')



# =========================
# Entry
# =========================
async def main():
    mp.set_start_method("spawn", force=True)

    stop_event = mp.Event()
    frame_q = mp.Queue(2)
    yolo_q = mp.Queue()
    display_q = mp.Queue(2)
    weight_q = mp.Queue()

    # ===== start processes =====
    p_capture = mp.Process(target=capture_process, args=(frame_q, stop_event))
    p_yolo    = mp.Process(target=yolo_process, args=(frame_q, yolo_q, display_q, stop_event))
    p_display = mp.Process(target=display_process, args=(display_q, stop_event))

    p_capture.start()
    p_yolo.start()
    p_display.start()

    # ===== start async tasks =====
    task_weight = asyncio.create_task(weight_worker(stop_event, weight_q))
    task_main   = asyncio.create_task(main_item_detection(stop_event, weight_q, yolo_q))

    try:
        await asyncio.gather(task_weight, task_main)
    finally:
        # Cancel any still-running async tasks
        task_weight.cancel()
        task_main.cancel()

        # ===== join & terminate processes =====
        print("🛑 Joining processes...")
        for p in (p_capture, p_yolo, p_display):
            if p.is_alive():
                p.join(timeout=1)
                if p.is_alive():
                    p.terminate()
        print("✅ All processes stopped")



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⏹ Stopped")
