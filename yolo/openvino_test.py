import multiprocessing as mp
from multiprocessing import shared_memory
from queue import Empty, Full
import time
import cv2
import numpy as np
import psutil
import openvino as ov 

# =========================
# Config - 性能全開配置
# =========================
MODEL_XML = r"F:\Degree_Final_Year_Project\V4_Retrain\yolo12_balanced_final_v22\weights\best_openvino_model\best.xml"
DEVICE = "AUTO" 

FRAME_W, FRAME_H = 640, 480
PROC_W, PROC_H = 320, 320 
SHM_SLOTS = 8 
FRAME_SHAPE = (SHM_SLOTS, FRAME_H, FRAME_W, 3)

CONF_THRESHOLD = 0.3
CLASS_NAMES =  ['Aluminium_Can', 'hand', 'paper', 'plastic']
IGNORE_LABELS = ["hand"]

# 硬體核心鎖定 (Ryzen 5 7535HS)
CORE_PRODUCER = [2]
CORE_UI = [4]
CORE_INFER = [6, 8, 10]

def bind_affinity(core_ids):
    try: psutil.Process().cpu_affinity(core_ids)
    except: pass

def safe_put(q, item):
    try: q.put_nowait(item)
    except Full:
        try: q.get_nowait(); q.put_nowait(item)
        except: pass

# =========================
# Process: 影像獲取 (修正解析度匹配)
# =========================
def producer_process(shm_name, idx_q, state, stop_evt):
    bind_affinity(CORE_PRODUCER)
    shm = shared_memory.SharedMemory(name=shm_name)
    frame_pool = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG")) 
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    slot = 0
    last_ts = time.time()
    try:
        while not stop_evt.is_set():
            ok, frame = cap.read()
            if not ok: continue
            
            # 🔴 核心修正：強制檢查並調整解析度以匹配共享記憶體
            if frame.shape[0] != FRAME_H or frame.shape[1] != FRAME_W:
                frame = cv2.resize(frame, (FRAME_W, FRAME_H), interpolation=cv2.INTER_NEAREST)

            now = time.time()
            frame_pool[slot] = frame
            
            dt = now - last_ts
            if dt > 0:
                state["cap_fps"].value = state["cap_fps"].value * 0.9 + (1.0/dt) * 0.1
            last_ts = now
            
            state["latest_slot"].value = slot
            safe_put(idx_q, (slot, now))
            slot = (slot + 1) % SHM_SLOTS
    finally:
        cap.release()
        shm.close()

# =========================
# Process: OpenVINO 推理
# =========================
def infer_process(shm_name, idx_q, meta_q, state, stop_evt):
    bind_affinity(CORE_INFER)
    shm = shared_memory.SharedMemory(name=shm_name)
    frame_pool = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)

    core = ov.Core()
    compiled_model = core.compile_model(MODEL_XML, DEVICE, {"PERFORMANCE_HINT": "THROUGHPUT"})
    output_layer = compiled_model.outputs[0]
    
    try:
        while not stop_evt.is_set():
            try:
                slot, ts = idx_q.get(timeout=0.1)
                while not idx_q.empty(): slot, ts = idx_q.get_nowait()
            except: continue

            # 使用較快的 NEAREST 插值進行預處理
            blob = cv2.resize(frame_pool[int(slot)], (PROC_W, PROC_H), interpolation=cv2.INTER_NEAREST)
            blob = blob.transpose(2, 0, 1)[None, ...].astype(np.float32) / 255.0

            t0 = time.time()
            results = compiled_model([blob])[output_layer]
            t1 = time.time()

            dets = []
            if results.ndim == 3:
                data = results[0].T 
                for row in data:
                    scores = row[4:]
                    cid = np.argmax(scores)
                    conf = scores[cid]
                    if conf > CONF_THRESHOLD:
                        label = CLASS_NAMES[cid] if cid < len(CLASS_NAMES) else "item"
                        if label.lower() in IGNORE_LABELS: continue
                        x, y, w, h = row[:4]
                        dets.append({
                            "xyxy": [int((x-w/2)*FRAME_W/PROC_W), int((y-h/2)*FRAME_H/PROC_H), 
                                     int((x+w/2)*FRAME_W/PROC_W), int((y+h/2)*FRAME_H/PROC_H)],
                            "conf": float(conf), "label": label
                        })

            state["inf_fps"].value = state["inf_fps"].value * 0.8 + (1.0/(t1-t0 if t1>t0 else 0.001)) * 0.2
            safe_put(meta_q, {"dets": dets})
    finally:
        shm.close()

# =========================
# Main UI (完全解除頻率限制)
# =========================
def main():
    mp.set_start_method("spawn", force=True)
    bind_affinity(CORE_UI)

    state = {
        "latest_slot": mp.Value("i", -1, lock=False),
        "cap_fps": mp.Value("d", 0.0, lock=False),
        "inf_fps": mp.Value("d", 0.0, lock=False),
    }
    stop_evt = mp.Event()
    idx_q, meta_q = mp.Queue(maxsize=1), mp.Queue(maxsize=1)
    shm = shared_memory.SharedMemory(create=True, size=int(np.prod(FRAME_SHAPE)))
    
    p_cap = mp.Process(target=producer_process, args=(shm.name, idx_q, state, stop_evt), daemon=True)
    p_inf = mp.Process(target=infer_process, args=(shm.name, idx_q, meta_q, state, stop_evt), daemon=True)
    p_cap.start(); p_inf.start()

    frame_pool = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)
    smoothed_boxes = {} 
    last_ui_ts = time.time()

    try:
        while True:
            loop_start = time.time()
            try:
                new_dets = meta_q.get_nowait()["dets"]
                current_labels = [d["label"] for d in new_dets]
                for d in new_dets:
                    lbl = d["label"]
                    if lbl not in smoothed_boxes: smoothed_boxes[lbl] = d
                    else:
                        for j in range(4):
                            smoothed_boxes[lbl]["xyxy"][j] = int(smoothed_boxes[lbl]["xyxy"][j] * 0.1 + d["xyxy"][j] * 0.9)
                        smoothed_boxes[lbl]["conf"] = d["conf"]
                smoothed_boxes = {k: v for k, v in smoothed_boxes.items() if k in current_labels}
            except Empty: pass

            slot = state["latest_slot"].value
            if slot >= 0:
                frame = frame_pool[slot].copy()
                for label, d in smoothed_boxes.items():
                    x1, y1, x2, y2 = d["xyxy"]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{label} {d['conf']:.2f}", (x1, max(25, y1-10)), 0, 0.6, (0, 255, 0), 2)

                now = time.time()
                ui_fps = 1.0 / (now - last_ui_ts) if now > last_ui_ts else 0
                last_ui_ts = now
                cv2.putText(frame, f"UI: {ui_fps:.1f} | AI: {state['inf_fps'].value:.1f} | Cap: {state['cap_fps'].value:.1f}", (10, 30), 0, 0.6, (0, 255, 255), 2)

                cv2.imshow("UNLOCKED - Ryzen 7535HS", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'): break
    finally:
        stop_evt.set()
        shm.close(); shm.unlink(); cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
