import cv2
import time
import multiprocessing as mp
import torch
from ultralytics import YOLO
from collections import Counter

MODEL_PATH = r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\secondTrain\Extra_retrain2\weights\best.engine"
Box_w = 400
Box_h = 400

def capture_process(frame_q, stop_event):
    cap = cv2.VideoCapture(0)
    while not stop_event.is_set():
        ret, frame = cap.read()
        if ret and not frame_q.full():
            frame_q.put(frame)
    cap.release()


def yolo_process(frame_q, result_q, shared_dict, stop_event):
    model = YOLO(MODEL_PATH, task='detect')
    printed_ids = set()  # persist across frames

    while not stop_event.is_set():
        if frame_q.empty():
            time.sleep(0.002)
            continue

        frame = frame_q.get()

        # -------- Center Box --------
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        x1 = cx - Box_w // 2
        y1 = cy - Box_h // 2
        x2 = cx + Box_w // 2
        y2 = cy + Box_h // 2
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # ----------------------------

        results = model.track(
            frame,
            persist=True,
            conf=0.25,
            iou=0.45,
            tracker="botsort.yaml",
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )

        for r in results:
            if r.boxes is None or r.boxes.id is None:
                continue

            boxes = r.boxes

            for xyxy, cls_id, track_id in zip(
                boxes.xyxy, boxes.cls, boxes.id
            ):
                bx1, by1, bx2, by2 = map(int, xyxy)
                obj_cx = (bx1 + bx2) // 2
                obj_cy = (by1 + by2) // 2

                class_id = int(cls_id.item())
                track_id = int(track_id.item())
                class_name = r.names[class_id]

                # Draw detection
                cv2.rectangle(frame, (bx1, by1), (bx2, by2), (255, 0, 0), 2)
                cv2.circle(frame, (obj_cx, obj_cy), 4, (0, 0, 255), -1)

                # Center box logic
                if x1 <= obj_cx <= x2 and y1 <= obj_cy <= y2:
                    if track_id not in printed_ids:
                        print(f"[CENTER DETECTED] ID {track_id}: {class_name}")
                        printed_ids.add(track_id)
                        shared_dict[track_id] = class_name

        if not result_q.full():
            result_q.put(frame)



def display_process(result_q, stop_event):
    fps_start, high_fps, avg_fps, loop =time.time(), 0, 0, 0 
    
    while not stop_event.is_set():
        if result_q.empty():
            time.sleep(0.005)
            continue
        
        frame = result_q.get()
        
        loop += 1
        now = time.time()
        fps = 1 / (now - fps_start)
        fps_start = now

        high_fps = max(high_fps, fps)

        if loop == 30:
            loop = 0
            avg_fps = fps if avg_fps == 0 else (avg_fps + fps) / 2
            
        cv2.putText(frame, f"Avg FPS: {avg_fps:.2f}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.putText(frame, f"High FPS: {high_fps:.2f}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("FPS Summary:")
            print(f"High FPS: {high_fps:.2f}")
            print(f"Avg FPS: {avg_fps:.2f}")

            stop_event.set()
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

    manager = mp.Manager()
    shared_dict = manager.dict()
    stop_event = mp.Event()

    frame_q = mp.Queue(maxsize=4)
    result_q = mp.Queue(maxsize=4)

    p_capture = mp.Process(target=capture_process, 
                        args=(frame_q, stop_event))
    
    p_yolo = mp.Process(target=yolo_process, 
                        args=(frame_q, result_q, shared_dict, stop_event))
    
    p_display = mp.Process(target=display_process, 
                        args=(result_q, stop_event))

    p_capture.start()
    p_yolo.start()
    p_display.start()

    p_display.join()

    # --- Tell all workers to stop ---
    stop_event.set()

    # --- Kill processes still alive (avoid hang) ---
    for p in [p_capture, p_yolo]:
        if p.is_alive():
            p.terminate()
            p.join(timeout=1)

    print("\nSummary of unique tracked objects:")
    for cls_name in set(shared_dict.values()):
        count = list(shared_dict.values()).count(cls_name)
        print(f"{cls_name}: {count}")
    i=0
    for track_id, class_name in shared_dict.items():
        i+=1
        print(f"{i}. ID {track_id}: {class_name}")

    print("\nSystem closed cleanly.")

    
    
