import cv2
import time
import multiprocessing as mp
import torch
from ultralytics import YOLO
from collections import Counter

MODEL_PATH = r"F:\Degree_Final_Year_Project\Degree_Final_Year_Project\material\pt\secondTrain\Extra_retrain2\weights\best.engine"

def capture_process(frame_q, stop_event):
    cap = cv2.VideoCapture(0)
    while not stop_event.is_set():
        ret, frame = cap.read()
        if ret and not frame_q.full():
            frame_q.put(frame)
    cap.release()


def detection(detect_q, result_q, shared_dict, stop_event):
    item_list=[]
    while not stop_event.is_set():
        r = detect_q.get()

        if r is None:
            continue

        boxes = r.boxes
        if boxes is None:
            continue

        ids = boxes.id
        cls = boxes.cls

        """
        
        計算如果weight_left有值的話，找出weight_left中出現次數最多的類別，並將該類別的track_id和class_name加入item_list和shared_dict中。
        temporay_list=[]
        if weight_left:
            len(temporay_list)=len(weight_left)
            temporary_count=Counter(temporay_list)
            top_class=temporary_count.most_common(1)[0][0]
            for track_id, class_id in zip(ids, cls):
                track_id = int(track_id.item())
                class_id = int(class_id.item())
                class_name = r.names[class_id]
                if class_name==top_class:
                    item_list.append((track_id, class_name))
                    shared_dict[track_id] = class_name
            
        """
        # 如果ids不為None，則將每個track_id和class_name加入item_list和shared_dict中
        if ids is not None:
            for track_id, class_id in zip(ids, cls):
                track_id = int(track_id.item())
                class_id = int(class_id.item())
                class_name = r.names[class_id]
                item_list.append((track_id, class_name))

                shared_dict[track_id] = class_name

        annotated = r.plot()

        if not result_q.full():
            result_q.put(annotated)


def yolo_process(frame_q, detect_q, stop_event):
    model = YOLO(MODEL_PATH, task='detect')

    while not stop_event.is_set():
        frame = frame_q.get()

        results = model.track(
            frame,
            stream=True,
            persist=True,
            conf=0.25,
            iou=0.45,
            tracker="botsort.yaml",
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )

        for r in results:
            if not detect_q.full():
                detect_q.put(r)


def display_process(result_q, stop_event):
    fps_start, high_fps, avg_fps, loop =0, 0, 0, 0 
    
    while not stop_event.is_set():
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
    detect_q = mp.Queue(maxsize=4)
    result_q = mp.Queue(maxsize=4)

    p_capture = mp.Process(target=capture_process, args=(frame_q, stop_event))
    p_yolo = mp.Process(target=yolo_process, args=(frame_q, detect_q, stop_event))
    p_detection = mp.Process(target=detection, args=(detect_q, result_q, shared_dict, stop_event))
    p_display = mp.Process(target=display_process, args=(result_q, stop_event))

    p_capture.start()
    p_yolo.start()
    p_detection.start()
    p_display.start()

    # --- Wait only for display() ---
    p_display.join()

    # --- Tell all workers to stop ---
    stop_event.set()

    # --- Kill processes still alive (avoid hang) ---
    for p in [p_capture, p_yolo, p_detection]:
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

    
    
