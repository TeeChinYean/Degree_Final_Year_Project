import cv2
import numpy as np
import onnxruntime as ort

# ==============================
# CONFIG
# ==============================
MODEL_PATH = r"F:\Degree_Final_Year_Project\runs\detect\train10\weights\best.onnx"

INPUT_SIZE = 640
CONF_THRES = 0.25
IOU_THRES = 0.45


# ==============================
# INIT ONNX
# ==============================
session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])

input_name = session.get_inputs()[0].name


# ==============================
# PREPROCESS
# ==============================
def preprocess(frame):
    h, w = frame.shape[:2]

    img = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0

    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)

    return img, (h, w)


# ==============================
# SIGMOID
# ==============================
def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# ==============================
# POSTPROCESS (YOLO ONNX)
# ==============================
def postprocess(pred, orig_shape):
    pred = np.squeeze(pred)

    # fix shape [84, N] → [N, 84]
    if pred.shape[0] < pred.shape[1]:
        pred = pred.T

    boxes = pred[:, :4]
    obj_conf = pred[:, 4]
    class_probs = pred[:, 5:]

    # sigmoid activation
    boxes = sigmoid(boxes)
    obj_conf = sigmoid(obj_conf)
    class_probs = sigmoid(class_probs)

    class_ids = np.argmax(class_probs, axis=1)
    class_scores = class_probs[np.arange(len(class_probs)), class_ids]
    scores = obj_conf * class_scores

    # filter
    mask = scores > CONF_THRES
    boxes = boxes[mask]
    scores = scores[mask]
    class_ids = class_ids[mask]

    if len(boxes) == 0:
        return []

    # xywh → xyxy
    boxes_xyxy = np.zeros_like(boxes)
    boxes_xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
    boxes_xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
    boxes_xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
    boxes_xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2

    # scale back
    h, w = orig_shape
    scale_x = w / INPUT_SIZE
    scale_y = h / INPUT_SIZE

    boxes_xyxy[:, [0, 2]] *= scale_x
    boxes_xyxy[:, [1, 3]] *= scale_y

    # NMS
    indices = cv2.dnn.NMSBoxes(
        boxes_xyxy.tolist(),
        scores.tolist(),
        CONF_THRES,
        IOU_THRES
    )

    results = []
    if len(indices) > 0:
        for i in indices.flatten():
            results.append((boxes_xyxy[i], scores[i], class_ids[i]))

    return results


# ==============================
# MAIN LOOP
# ==============================
def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Camera not found")
        return

    print("✅ ONNX YOLO Camera started... Press Q to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        orig_frame = frame.copy()

        # inference
        input_tensor, orig_shape = preprocess(frame)

        outputs = session.run(None, {input_name: input_tensor})
        pred = outputs[0]

        detections = postprocess(pred, orig_shape)

        # draw
        for box, score, cls_id in detections:
            x1, y1, x2, y2 = map(int, box)

            cv2.rectangle(orig_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            cv2.putText(
                orig_frame,
                f"ID:{cls_id} {score:.2f}",
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1
            )

        cv2.imshow("ONNX YOLO Camera", orig_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()