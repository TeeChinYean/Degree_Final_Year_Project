import multiprocessing as mp
from multiprocessing import shared_memory
from queue import Empty, Full
import time
import cv2
import numpy as np
import psutil
import openvino as ov

# =========================
# Config - 全 320 统一配置
# =========================
MODEL_XML = r"F:\Degree_Final_Year_Project\V4_Retrain\yolo12_balanced_final_v22\weights\best_openvino_model\best.xml"
DEVICE = "CPU" 

FRAME_W, FRAME_H = 320, 240
PROC_W, PROC_H = 320, 320 
SHM_SLOTS = 8 
FRAME_SHAPE = (SHM_SLOTS, FRAME_H, FRAME_W, 3)

CONF_THRESHOLD = 0.3
CLASS_NAMES = ['Aluminium_Can', 'hand', 'paper', 'plastic']
IGNORE_LABELS = ["hand"]

DISPLAY_FPS = 60
FRAME_TIME = 1.0 / DISPLAY_FPS
ALPHA = 0.15 

# 核心分配计划 (Ryzen 5 7535HS)
CORE_PRODUCER = [2]
CORE_UI = [4]
CORE_INFER_A = [6, 7]
CORE_INFER_B = [8, 9]

def bind_affinity(core_ids):
    try: psutil.Process().cpu_affinity(core_ids)
    except: pass

# =========================
# 推理工人 (并行执行)
# =========================
def infer_worker(shm_name, task_q, meta_q, core_ids, stop_evt):
    bind_affinity(core_ids)
    shm = shared_memory.SharedMemory(name=shm_name)
    frame_pool = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)

    core = ov.Core()
    compiled_model = core.compile_model(MODEL_XML, DEVICE)
    infer_request = compiled_model.create_infer_request()
    input_layer = compiled_model.input(0)

    try:
        while not stop_evt.is_set():
            try:
                # 获取任务
                slot = task_q.get(timeout=0.1)
            except Empty: continue

            # 手动预处理
            raw_frame = frame_pool[slot]
            blob = cv2.resize(raw_frame, (PROC_W, PROC_H))
            blob = blob.transpose(2, 0, 1)[None, ...].astype(np.float32) / 255.0

            t0 = time.time()
            infer_request.infer({input_layer: blob})
            results = infer_request.get_output_tensor().data
            t1 = time.time()

            dets = []
            if results.ndim == 3:
                data = results[0].T 
                for row in data:
                    conf = row[4:].max()
                    if conf > CONF_THRESHOLD:
                        cid = row[4:].argmax()
                        label = CLASS_NAMES[cid] if cid < len(CLASS_NAMES) else "item"
                        if label.lower() in IGNORE_LABELS: continue
                        x, y, w, h = row[:4]
                        dets.append({
                            "xyxy": [(x-w/2)*FRAME_W/PROC_W, (y-h/2)*FRAME_H/PROC_H, 
                                     (x+w/2)*FRAME_W/PROC_W, (y+h/2)*FRAME_H/PROC_H],
                            "conf": float(conf), "label": label
                        })
            
            # 将结果放入队列
            try:
                meta_q.put_nowait({"dets": dets, "fps": 1.0/(t1-t0)})
            except Full:
                try:
                    meta_q.get_nowait()
                    meta_q.put_nowait({"dets": dets, "fps": 1.0/(t1-t0)})
                except: pass
    finally:
        shm.close()

# =========================
# 生产者：动态负载平衡分发
# =========================
def producer_process(shm_name, q_a, q_b, state, stop_evt):
    bind_affinity(CORE_PRODUCER)
    shm = shared_memory.SharedMemory(name=shm_name)
    frame_pool = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    frame_count = 0
    try:
        while not stop_evt.is_set():
            ok, frame = cap.read()
            if not ok: continue
            
            if frame.shape[0] != FRAME_H or frame.shape[1] != FRAME_W:
                frame = cv2.resize(frame, (FRAME_W, FRAME_H), interpolation=cv2.INTER_NEAREST)

            slot = frame_count % SHM_SLOTS
            frame_pool[slot] = frame
            state["latest_slot"].value = slot

            # --- 改进：动态分发逻辑 (空闲优先) ---
            # 优先检查 A 是否有空，其次 B
            if q_a.empty():
                try: q_a.put_nowait(slot)
                except Full: pass
            elif q_b.empty():
                try: q_b.put_nowait(slot)
                except Full: pass
            else:
                # 如果都满了，强制塞入一个（由队列 maxsize=1 保证覆盖旧任务）
                try: q_a.put_nowait(slot)
                except Full:
                    try: q_a.get_nowait(); q_a.put_nowait(slot)
                    except: pass

            frame_count += 1
    finally:
        cap.release()
        shm.close()

# =========================
# UI 进程：最新结果优先
# =========================
def main():
    mp.set_start_method("spawn", force=True)
    bind_affinity(CORE_UI)

    state = {"latest_slot": mp.Value("i", -1, lock=False)}
    stop_evt = mp.Event()
    
    # 任务分发队列，大小设为 1 确保实时性
    q_a = mp.Queue(maxsize=1)
    q_b = mp.Queue(maxsize=1)
    # 结果队列，设大一点以防 90FPS 下溢出，但处理时只取最新
    meta_q = mp.Queue(maxsize=10)
    
    shm = shared_memory.SharedMemory(create=True, size=int(np.prod(FRAME_SHAPE)))
    
    processes = [
        mp.Process(target=producer_process, args=(shm.name, q_a, q_b, state, stop_evt)),
        mp.Process(target=infer_worker, args=(shm.name, q_a, meta_q, CORE_INFER_A, stop_evt)),
        mp.Process(target=infer_worker, args=(shm.name, q_b, meta_q, CORE_INFER_B, stop_evt))
    ]
    
    for p in processes: p.start()

    frame_pool = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)
    smooth_dets = {} 
    last_display_time = time.time()
    avg_ai_fps = 0

    try:
        while True:
            current_time = time.time()

            # --- 改进：消费最新结果策略 (清理队列积压) ---
            res = None
            try:
                while not meta_q.empty():
                    res = meta_q.get_nowait() # 循环 get 直到拿到最后（最新）一个
                
                if res is not None:
                    raw_data = res["dets"]
                    avg_ai_fps = avg_ai_fps * 0.9 + (res["fps"] * 2) * 0.1 
                    active_labels = set()
                    for d in raw_data:
                        lbl = d["label"]
                        active_labels.add(lbl)
                        raw_box = np.array(d["xyxy"])
                        if lbl not in smooth_dets:
                            smooth_dets[lbl] = {"box": raw_box, "conf": d["conf"]}
                        else:
                            smooth_dets[lbl]["box"] = smooth_dets[lbl]["box"] * (1 - ALPHA) + raw_box * ALPHA
                            smooth_dets[lbl]["conf"] = d["conf"]
                    smooth_dets = {k: v for k, v in smooth_dets.items() if k in active_labels}
            except Empty: pass

            # 60 FPS 渲染控制
            if current_time - last_display_time >= FRAME_TIME:
                slot = state["latest_slot"].value
                if slot >= 0:
                    frame = frame_pool[slot].copy()
                    for lbl, data in smooth_dets.items():
                        x1, y1, x2, y2 = data["box"].astype(int)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
                        cv2.putText(frame, lbl, (x1, max(15, y1-5)), 0, 0.4, (0, 255, 0), 1)

                    cv2.putText(frame, f"Parallel Balanced | Total AI: {avg_ai_fps:.1f}", (5, 15), 0, 0.4, (0, 255, 255), 1)
                    cv2.imshow("Optimized Display", frame)
                    last_display_time = current_time

                if cv2.waitKey(1) & 0xFF == ord('q'): break
            
            time.sleep(0.001)

    finally:
        stop_evt.set()
        for p in processes: p.join()
        shm.close(); shm.unlink(); cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
