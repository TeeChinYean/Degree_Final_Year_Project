import cv2
import asyncio
import multiprocessing as mp
from multiprocessing import shared_memory
from queue import Empty, Full
from collections import Counter
import threading
from threading import Lock
import numpy as np
import openvino as ov
import psutil

import time
import serial
import json
import re
import os
import sys
import uuid

import socketio
import base64

from flask import Flask, Response, request, jsonify
from flask_cors import CORS

admin_enabled = True # Global flag to lock/unlock the site from Admin

import keyboard

# Global variables
data_list = []
data_lock = Lock()
active_event = mp.Event()
active_event.clear()  

# =========================
# Site Configuration
# =========================
import subprocess

def _get_base_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_site_config() -> dict:
    """Load full station config from site_config.json. Generate defaults if missing."""
    base_dir   = _get_base_dir()
    config_path = os.path.join(base_dir, "site_config.json")
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except Exception as e:
            print(f"[CONFIG] Error reading site config: {e}")

    changed = False
    if "SITE_ID" not in config:
        config["SITE_ID"] = f"Site_{uuid.uuid4().hex[:6].upper()}"
        changed = True
    if "ADMIN_SERVER_URL" not in config:
        config["ADMIN_SERVER_URL"] = "http://100.83.94.86:5001"
        changed = True
    if "CAMERA_INDEX" not in config:
        config["CAMERA_INDEX"] = 0
        changed = True
    if "RTSP_PORT" not in config:
        config["RTSP_PORT"] = 8554
        changed = True
    if "STATION_IP" not in config:
        config["STATION_IP"] = ""
        changed = True
    if "ADMIN_TAILSCALE_IP" not in config:
        config["ADMIN_TAILSCALE_IP"] = "100.83.94.86" 
        changed = True
    if "CAM_STREAM_PORT" not in config:
        config["CAM_STREAM_PORT"] = 55200               # ← dedicated port for raw camera
        changed = True

    if changed:
        try:
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"[CONFIG] Error writing site config: {e}")
    return config

def get_local_ip() -> str:
    """Return the best-guess Tailscale/local IP for this machine."""
    import socket as _socket
    try:
        hostname = _socket.gethostname()
        addrs = _socket.getaddrinfo(hostname, None)
        for addr in addrs:
            ip = addr[4][0]
            if ip.startswith('100.'):
                return ip
    except Exception:
        pass
    try:
        s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# Load config at startup
_SITE_CFG           = get_site_config()
SITE_ID             = _SITE_CFG["SITE_ID"]
STATION_NAME        = _SITE_CFG.get("STATION_NAME", SITE_ID)
ADMIN_SERVER_URL    = _SITE_CFG["ADMIN_SERVER_URL"]
CAMERA_INDEX        = int(_SITE_CFG.get("CAMERA_INDEX", 0))
RTSP_PORT           = int(_SITE_CFG.get("RTSP_PORT", 8554))
STATION_IP          = _SITE_CFG.get("STATION_IP") or get_local_ip()
ADMIN_TAILSCALE_IP  = _SITE_CFG.get("ADMIN_TAILSCALE_IP", "100.83.94.86")   
CAM_STREAM_PORT     = int(_SITE_CFG.get("CAM_STREAM_PORT", 55200))          

print(f"[CONFIG] Site ID: {SITE_ID}  |  Admin: {ADMIN_SERVER_URL}")
print(f"[CONFIG] Station IP: {STATION_IP}  |  Camera: {CAMERA_INDEX}  |  RTSP port: {RTSP_PORT}")
print(f"[CONFIG] Raw cam stream -> {ADMIN_TAILSCALE_IP}:{CAM_STREAM_PORT}")   # <- NEW

sio_client = socketio.Client()

# =========================
# RTSP Push (mediamtx + FFmpeg)
# =========================
_mediamtx_proc = None
_ffmpeg_proc   = None
_rtsp_active   = False

def _find_binary(name: str) -> str:
    """Search for a binary next to the exe (bundled) or in PATH."""
    base_dir = _get_base_dir()
    # When frozen, PyInstaller places binaries in _internal/ or same dir
    for candidate in [
        os.path.join(base_dir, name),
        os.path.join(base_dir, "_internal", name),
        os.path.join(os.path.dirname(base_dir), name),
    ]:
        if os.path.isfile(candidate):
            return candidate
    return name  # Fall back to PATH

def start_mediamtx() -> bool:
    """Launch bundled mediamtx.exe. Returns True if started successfully."""
    global _mediamtx_proc
    mtx = _find_binary("mediamtx.exe")
    try:
        _mediamtx_proc = subprocess.Popen(
            [mtx],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        time.sleep(1.5)  # Give mediamtx time to start
        print(f"[RTSP] mediamtx started (pid={_mediamtx_proc.pid})")
        return True
    except FileNotFoundError:
        print(f"[RTSP] mediamtx.exe not found at '{mtx}' — RTSP disabled")
        return False
    except Exception as e:
        print(f"[RTSP] Failed to start mediamtx: {e}")
        return False

def start_rtsp_ffmpeg(width: int, height: int, fps: int = 15):
    """Open FFmpeg subprocess that reads raw BGR frames from stdin and pushes RTSP to both /live and /camera."""
    global _ffmpeg_proc
    ffmpeg = _find_binary("ffmpeg.exe")
    rtsp_live   = f"rtsp://localhost:{RTSP_PORT}/live"
    rtsp_camera = f"rtsp://localhost:{RTSP_PORT}/camera"
    cmd = [
        ffmpeg, "-y",
        "-f",       "rawvideo",
        "-vcodec",  "rawvideo",
        "-pix_fmt", "bgr24",
        "-s",       f"{width}x{height}",
        "-r",       str(fps),
        "-i",       "pipe:0",
        "-c:v",     "libx264",
        "-preset",  "ultrafast",
        "-tune",    "zerolatency",
        "-f",       "rtsp",
        rtsp_live,
        "-c:v",     "copy",
        "-f",       "rtsp",
        rtsp_camera,
    ]
    try:
        _ffmpeg_proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        print(f"[RTSP] FFmpeg pushing to {rtsp_live} and {rtsp_camera} (pid={_ffmpeg_proc.pid})")
        return _ffmpeg_proc
    except FileNotFoundError:
        print(f"[RTSP] ffmpeg.exe not found at '{ffmpeg}' — RTSP disabled")
        return None
    except Exception as e:
        print(f"[RTSP] FFmpeg start failed: {e}")
        return None

def push_frame_rtsp(frame):
    """Write a single BGR frame to the FFmpeg stdin pipe."""
    global _ffmpeg_proc, _rtsp_active
    if _ffmpeg_proc and _ffmpeg_proc.stdin:
        try:
            _ffmpeg_proc.stdin.write(frame.tobytes())
        except (BrokenPipeError, OSError):
            _rtsp_active = False
            _ffmpeg_proc = None

# =========================
# Site Relay (Socket.IO + RTSP fallback)
# =========================
def relay_worker(active_event, relay_q):
    global _rtsp_active
    connected = False

    @sio_client.on('connect')
    def on_connect():
        print(f"[RELAY] Connected to Admin server at {ADMIN_SERVER_URL}")
        sio_client.emit('register_site', {
            'site_id':    SITE_ID,
            'station_ip': STATION_IP,
            'rtsp_port':  RTSP_PORT,
        })

    @sio_client.on('control_command')
    def on_control(data):
        global admin_enabled
        action = data.get('action')
        if action == 'enable':
            admin_enabled = True
            print("[ADMIN] Admin ENABLED the site.")
        elif action == 'disable':
            admin_enabled = False
            active_event.clear()
            print("[ADMIN] Admin DISABLED the site.")

    def connect_sio():
        nonlocal connected
        if not connected:
            try:
                sio_client.connect(ADMIN_SERVER_URL)
                connected = True
            except Exception:
                pass

    while True:
        connect_sio()
        try:
            frame = relay_q.get(timeout=0.1)
            if frame is None:
                continue

            # === PRIMARY: push frame to RTSP via FFmpeg stdin ===
            if _rtsp_active:
                push_frame_rtsp(frame)

            if connected:
                ok, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ok:
                    b64_img = base64.b64encode(buffer).decode('utf-8')
                    try:
                        sio_client.emit('video_frame', {'site_id': SITE_ID, 'image': b64_img})
                    except Exception:
                        connected = False
        except Empty:
            continue
        except Exception:
            connected = False


# =========================
# ── NEW: Raw Camera Relay over Tailscale TCP ──────────────────────────────────
#
# Goal : stream RAW (no YOLO overlay) MJPEG frames from the station camera
#        directly to admin_video_server.py over a persistent Tailscale TCP
#        connection.  Detection code is completely untouched.
#
# Protocol (same length-prefix idea as tailscale_pc_*.py):
#   Handshake  →  station sends JSON {"type":"cam_register","site_id":"..."}
#   Per frame  →  4-byte big-endian length  +  raw JPEG bytes
#   Admin acks are not required; this is a push-only stream.
#
# The raw_cam_q is fed by capture_process (raw frames, before YOLO draws).
# =========================

import struct as _struct
import socket as _socket

CAM_TCP_FPS          = 15          # Max FPS sent to admin
CAM_TCP_JPEG_QUALITY = 55          # JPEG quality for the admin raw stream
CAM_TCP_RECONNECT_S  = 5           # Seconds between reconnect attempts


def _send_cam_frame(sock: _socket.socket, jpeg_bytes: bytes) -> bool:
    """Send one JPEG frame prefixed with 4-byte big-endian length.
    Returns False if the socket is broken."""
    try:
        header = _struct.pack(">I", len(jpeg_bytes))
        sock.sendall(header + jpeg_bytes)
        return True
    except (BrokenPipeError, OSError, ConnectionResetError):
        return False


def raw_cam_relay_worker(raw_cam_q: mp.Queue):
    """
    Daemon thread: reads raw (no-overlay) frames from raw_cam_q and streams
    them over a persistent TCP connection to admin_video_server.py.

    Reconnects automatically whenever the connection drops.
    This worker never touches detection queues or active_event.
    """
    frame_interval = 1.0 / CAM_TCP_FPS
    last_frame_t   = 0.0
    sock           = None

    def _connect() -> _socket.socket | None:
        try:
            s = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((ADMIN_TAILSCALE_IP, CAM_STREAM_PORT))
            # Handshake: identify this station
            handshake = json.dumps({
                "type":    "cam_register",
                "site_id": SITE_ID,
                "station_ip": STATION_IP,
            }).encode("utf-8")
            s.sendall(_struct.pack(">I", len(handshake)) + handshake)
            s.settimeout(None)   # blocking mode after handshake
            print(f"[CAM-TCP] Connected to admin {ADMIN_TAILSCALE_IP}:{CAM_STREAM_PORT}")
            return s
        except Exception as e:
            print(f"[CAM-TCP] Connect failed: {e}  — retrying in {CAM_TCP_RECONNECT_S}s")
            return None

    while True:
        # ── Ensure we have a live socket ─────────────────────────────────────
        if sock is None:
            sock = _connect()
            if sock is None:
                time.sleep(CAM_TCP_RECONNECT_S)
                continue

        # ── Drain the queue, keep only the freshest frame ────────────────────
        frame = None
        try:
            # Non-blocking drain so we always send the latest frame
            while True:
                frame = raw_cam_q.get_nowait()
        except Exception:
            pass   # queue is now empty

        if frame is None:
            # Nothing new yet — wait briefly
            try:
                frame = raw_cam_q.get(timeout=0.1)
            except Exception:
                continue

        # ── Rate-limit ───────────────────────────────────────────────────────
        now = time.time()
        if now - last_frame_t < frame_interval:
            continue
        last_frame_t = now

        # ── Encode and send ──────────────────────────────────────────────────
        # Downscale slightly to save bandwidth (half resolution)
        h, w = frame.shape[:2]
        small = cv2.resize(frame, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(
            '.jpg', small,
            [int(cv2.IMWRITE_JPEG_QUALITY), CAM_TCP_JPEG_QUALITY]
        )
        if not ok:
            continue

        if not _send_cam_frame(sock, buf.tobytes()):
            print("[CAM-TCP] Connection lost — reconnecting…")
            try:
                sock.close()
            except Exception:
                pass
            sock = None


# =========================
# Camera & YOLO Class
# =========================
# settings
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    BASE_DIR = os.path.dirname(sys.executable)
    # PyInstaller 6+ puts data files inside _internal/
    _internal_dir = os.path.join(BASE_DIR, "_internal")
    if os.path.isdir(_internal_dir):
        BASE_DIR = _internal_dir
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_XML = os.path.join(BASE_DIR, "best_openvino_model", "best.xml")
DEVICE = "CPU"
FRAME_W = 640
FRAME_H = 480
PROC_W = 320 #256 for 100fps
PROC_H = 256 #256 for 100fps
SHM_SLOTS = 8
FRAME_SHAPE = (SHM_SLOTS, FRAME_H, FRAME_W, 3)
CONF_THRESHOLD = 0.3
MAX_DRAW_DETS = 2
HUD_UPDATE_INTERVAL = 0.12
CLASS_NAMES = ['Aluminium_Can', 'hand', 'paper', 'plastic']
IGNORE_LABELS = {"hand"}
BOX_SIZE = 480
STREAM_JPEG_QUALITY = 90
STREAM_SCALE = 1.0
DISPLAY_FPS = 60
FRAME_TIME = 1.0 / DISPLAY_FPS
ALPHA = 0.15

# CPU affinity profile (mirrors test_openvino.py idea)
CORE_PRODUCER = [2]
CORE_UI = [4]
CORE_INFER_A = [6, 7]
CORE_INFER_B = [8, 9]
CORE_INFER_C = [10, 11]

def bind_affinity(core_ids):
    try:
        psutil.Process().cpu_affinity(core_ids)
    except Exception:
        pass

class ItemDetect:
    def __init__(self, yolo_q, display_q, relay_q, active_event, raw_cam_q=None):  # ← raw_cam_q added
        self.yolo_q    = yolo_q
        self.display_q = display_q
        self.relay_q   = relay_q
        self.active_event = active_event
        self.raw_cam_q = raw_cam_q   # ← NEW: receives raw frames for admin cam view
    
    @staticmethod
    def safe_put(q, item):
        try:
            q.put_nowait(item)
        except Full:
            try:
                q.get_nowait()
                q.put_nowait(item)
            except Exception:
                pass

    def capture_process(self, shm_name, q_a, q_b, q_c, state, stop_evt):
        bind_affinity(CORE_PRODUCER)
        shm = shared_memory.SharedMemory(name=shm_name)
        frame_pool = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)
        cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        print("[CAM] Camera capture running continuously")
        frame_count = 0

        try:
            while not stop_evt.is_set():
                success, frame = cap.read()
                if not success:
                    time.sleep(0.01)
                    continue

                if frame.shape[0] != FRAME_H or frame.shape[1] != FRAME_W:
                    frame = cv2.resize(frame, (FRAME_W, FRAME_H), interpolation=cv2.INTER_NEAREST)

                slot = frame_count % SHM_SLOTS
                frame_pool[slot] = frame
                state["latest_slot"].value = slot

                # ── NEW: push raw frame to admin cam relay (always, even inactive) ──
                if self.raw_cam_q is not None:
                    self.safe_put(self.raw_cam_q, frame.copy())

                if q_a.empty():
                    self.safe_put(q_a, slot)
                elif q_b.empty():
                    self.safe_put(q_b, slot)
                elif q_c.empty():
                    self.safe_put(q_c, slot)
                else:
                    self.safe_put(q_a, slot)

                frame_count += 1
        finally:
            cap.release()
            shm.close()

    def infer_worker(self, shm_name, task_q, meta_q, core_ids, stop_evt):
        bind_affinity(core_ids)
        shm = shared_memory.SharedMemory(name=shm_name)
        frame_pool = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)

        # Verify model file exists before loading
        if not os.path.isfile(MODEL_XML):
            print(f"[ERROR] Model not found: {MODEL_XML}")
            return

        core = ov.Core()
        print(f"[INFO] Available OpenVINO devices: {core.available_devices}")
        print(f"[START] Loading model on {DEVICE}: {MODEL_XML}")

        # Intel CPU config: let OpenVINO pick optimal thread count automatically
        cpu_cfg = {
            "PERFORMANCE_HINT": "LATENCY",
            "INFERENCE_NUM_THREADS": str(max(1, len(core_ids))),
        }
        try:
            compiled_model = core.compile_model(MODEL_XML, "CPU", cpu_cfg)
            print(f"[OK] Model compiled on CPU with config: {cpu_cfg}")
        except RuntimeError as e:
            print(f"[WARN] CPU config unsupported, trying plain CPU compile: {e}")
            try:
                compiled_model = core.compile_model(MODEL_XML, "CPU")
                print("[OK] Model compiled on CPU (default config)")
            except Exception as e2:
                print(f"[ERROR] Failed to compile model: {e2}")
                return
        infer_request = compiled_model.create_infer_request()
        input_layer = compiled_model.input(0)

        try:
            while not stop_evt.is_set():
                if not self.active_event.is_set():
                    time.sleep(0.01)
                    continue
                try:
                    slot = task_q.get(timeout=0.1)
                except Empty:
                    continue

                raw_frame = frame_pool[int(slot)]
                if raw_frame.shape[1] == PROC_W and raw_frame.shape[0] == PROC_H:
                    proc_frame = raw_frame
                else:
                    proc_frame = cv2.resize(raw_frame, (PROC_W, PROC_H), interpolation=cv2.INTER_NEAREST)
                blob = proc_frame.transpose(2, 0, 1)[None, ...].astype(np.float32) / 255.0

                t0 = time.time()
                infer_request.infer({input_layer: blob})
                results = infer_request.get_output_tensor().data
                t1 = time.time()

                dets = []
                if results.ndim == 3:
                    data = results[0].T
                    if data.shape[0] > 0:
                        scores = data[:, 4:]
                        class_ids = np.argmax(scores, axis=1)
                        confs = scores[np.arange(scores.shape[0]), class_ids]
                        valid = confs > CONF_THRESHOLD
                        if np.any(valid):
                            rows = data[valid]
                            class_ids = class_ids[valid]
                            confs = confs[valid]
                            xs = rows[:, 0]
                            ys = rows[:, 1]
                            bws = rows[:, 2]
                            bhs = rows[:, 3]
                            for i in range(len(confs)):
                                cid = int(class_ids[i])
                                label = CLASS_NAMES[cid] if cid < len(CLASS_NAMES) else "item"
                                if label.lower() in IGNORE_LABELS:
                                    continue
                                x = xs[i]
                                y = ys[i]
                                bw = bws[i]
                                bh = bhs[i]
                                dets.append({
                                    "xyxy": [
                                        (x - bw / 2) * FRAME_W / PROC_W,
                                        (y - bh / 2) * FRAME_H / PROC_H,
                                        (x + bw / 2) * FRAME_W / PROC_W,
                                        (y + bh / 2) * FRAME_H / PROC_H,
                                    ],
                                    "conf": float(confs[i]),
                                    "label": label,
                                })

                fps = 1.0 / (t1 - t0) if t1 > t0 else 0.0
                self.safe_put(meta_q, {"dets": dets, "fps": fps, "ts": t1})
        finally:
            shm.close()

    def ui_process(self, shm_name, meta_q, state, stop_evt):
        bind_affinity(CORE_UI)
        shm = shared_memory.SharedMemory(name=shm_name)
        frame_pool = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)

        smooth_dets = {}
        label_emit_ts = {}
        yolo_emit_cooldown = 0.15
        last_display_time = time.time()

        try:
            while not stop_evt.is_set():

                # consume queue and keep only the latest detections for display
                res = None
                try:
                    while not meta_q.empty():
                        res = meta_q.get_nowait()
                except Empty:
                    res = None

                if res is not None:
                    raw_data = res["dets"]
                    active_labels = set()
                    for d in raw_data:
                        lbl = d["label"]
                        active_labels.add(lbl)
                        raw_box = np.array(d["xyxy"], dtype=np.float32)
                        if lbl not in smooth_dets:
                            smooth_dets[lbl] = {"box": raw_box, "conf": d["conf"]}
                        else:
                            smooth_dets[lbl]["box"] = smooth_dets[lbl]["box"] * (1 - ALPHA) + raw_box * ALPHA
                            smooth_dets[lbl]["conf"] = d["conf"]
                    smooth_dets = {k: v for k, v in smooth_dets.items() if k in active_labels}

                now = time.time()
                if now - last_display_time < FRAME_TIME:
                    time.sleep(0.001)
                    continue
                last_display_time = now

                slot = state["latest_slot"].value
                if slot < 0:
                    continue
                frame = frame_pool[int(slot)].copy()

                h, w, _ = frame.shape
                x1, y1 = w // 2 - BOX_SIZE // 2, h // 2 - BOX_SIZE // 2
                x2, y2 = w // 2 + BOX_SIZE // 2, h // 2 + BOX_SIZE // 2
                current_time = time.time()
                draw_count = 0
                for lbl, data in smooth_dets.items():
                    if draw_count >= MAX_DRAW_DETS:
                        break
                    l, t, r, b = data["box"].astype(int)
                    xc = (l + r) / 2
                    yc = (t + b) / 2
                    if x1 < xc < x2 and y1 < yc < y2:
                        last_sent = label_emit_ts.get(lbl, 0.0)
                        if current_time - last_sent >= yolo_emit_cooldown:
                            self.yolo_q.put({"label": lbl, "time": current_time})
                            label_emit_ts[lbl] = current_time

                    cv2.rectangle(frame, (l, t), (r, b), (255, 0, 0), 1)
                    cv2.putText(frame, f"{lbl} {data['conf']:.2f}", (l, max(15, t - 5)), 0, 0.45, (255, 0, 0), 1)
                    draw_count += 1

                self.safe_put(self.display_q, frame)
                if self.relay_q is not None:
                    self.safe_put(self.relay_q, frame)
        finally:
            shm.close()

# =========================
# Web App
# =========================
# settings
app = Flask(__name__)
CORS(app)
def flask_video_stream():
    global display_q, active_event
    
    while True: # Always run to show video locally
        try:
            frame = display_q.get(timeout=0.1)
            
        except:
            continue
        
        
        if frame is None:
                time.sleep(0.1)
                continue

        if STREAM_SCALE != 1.0:
            frame = cv2.resize(frame, (0, 0), fx=STREAM_SCALE, fy=STREAM_SCALE, interpolation=cv2.INTER_AREA)
        #display frame in Flask(web)
        ok, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), STREAM_JPEG_QUALITY])
        if not ok:
            continue
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
    print("[CLEAR] Data cleared by user action")
    return jsonify({"status": "cleared"})


# Provide status to the local frontend
@app.route("/system_status", methods=["GET"])
def system_status():
    return jsonify({
        "admin_enabled": admin_enabled,
        "station_ip": STATION_IP,
        "site_id": SITE_ID,
        "station_name": STATION_NAME
    }), 200

@app.route("/activate", methods=["POST"])
def activate():
    if not admin_enabled:
        return jsonify({"error": "Site disabled by Admin", "status": "disabled"}), 403

    # force=True ignores the Content-Type header if it's missing
    data = request.get_json(force=True, silent=True) 
    is_active = data.get("active") if data else None

    if is_active is True:
        active_event.set()
        print("Activated", flush=True)
        return jsonify({"status": "activated"}), 200
    elif is_active is False:
        active_event.clear()
        print("Deactivated", flush=True)
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

    for port in ("COM7", "COM11", "COM8", "COM6", "COM3"):
        try:
            ser = serial.Serial(port, 9600, timeout=0.1)
            ser.write(b'\n')
            ser.reset_input_buffer()
            print(f"[OK] Weight sensor connected on {port}")
            break
        except:
            pass

    if not ser:
        print("[ERROR] Weight sensor not found — running without scale")
        while True:
            await asyncio.sleep(1)  # keep task alive so gather() doesn't exit

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
                        print(f"[ON] START id={weight_id} | weight={weight:.2f}")

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

                            print(f"[OFF] END   id={weight_id} | weight={avg_weight:.2f}")
                        else:
                            # Too short, reset but don't send end event 
                            weight_active = False

                buffer = ""

            await asyncio.sleep(0.02)

    finally:
        print("[SCALE] Closing serial port")
        ser.close()


# =========================
# Parallel Main Controller
# =========================
async def main_item_detection(active_event, weight_q, yolo_q):
    session = None
    print("[OK] Main controller started")

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
        print("[ERROR] No YOLO detection during weight event")
        return

    item, freq = Counter(labels).most_common(1)[0] #most appear label
    duration = s["we"] - s["ws"]

    if duration < MIN_YOLO_DURATION:
        print(f"[ERROR] Item detection too short ({duration:.2f}s)")
        return

    final_weight = s["weight_end"]
    print("\n[OK] FINAL RESULT")
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

    global active_event, display_q, _rtsp_active

    display_q  = mp.Queue(2)
    relay_q    = mp.Queue(2)
    yolo_q     = mp.Queue()
    weight_q   = mp.Queue()
    raw_cam_q  = mp.Queue(maxsize=2)   # ← NEW: raw frames for admin camera view
    q_a = mp.Queue(maxsize=1)
    q_b = mp.Queue(maxsize=1)
    q_c = mp.Queue(maxsize=1)
    meta_q = mp.Queue(maxsize=10)
    state  = {"latest_slot": mp.Value("i", -1, lock=False)}
    stop_evt = mp.Event()
    shm = shared_memory.SharedMemory(create=True, size=int(np.prod(FRAME_SHAPE)))

    # Item detection class — pass raw_cam_q so capture_process can feed it
    item_detect = ItemDetect(yolo_q, display_q, relay_q, active_event, raw_cam_q=raw_cam_q)  
    p_capture = mp.Process(target=item_detect.capture_process,
                           args=(shm.name, q_a, q_b, q_c, state, stop_evt))
    p_infer_a = mp.Process(target=item_detect.infer_worker,
                           args=(shm.name, q_a, meta_q, CORE_INFER_A, stop_evt))
    p_infer_b = mp.Process(target=item_detect.infer_worker,
                           args=(shm.name, q_b, meta_q, CORE_INFER_B, stop_evt))
    p_infer_c = mp.Process(target=item_detect.infer_worker,
                           args=(shm.name, q_c, meta_q, CORE_INFER_C, stop_evt))
    p_ui = mp.Process(target=item_detect.ui_process,
                      args=(shm.name, meta_q, state, stop_evt))
    p_capture.start()
    p_infer_a.start()
    p_infer_b.start()
    p_infer_c.start()
    p_ui.start()

    # ── RTSP push setup ───────────────────────────────────────────────────────
    # Try to start mediamtx RTSP server + FFmpeg push pipeline.
    # Falls back to Socket.IO Base64 if either binary is unavailable.
    if start_mediamtx():
        ffmpeg_proc = start_rtsp_ffmpeg(width=FRAME_W, height=FRAME_H, fps=15)
        if ffmpeg_proc:
            _rtsp_active = True
            print("[RTSP] Primary RTSP push active.")
        else:
            print("[RTSP] FFmpeg unavailable — using Socket.IO fallback.")
    else:
        print("[RTSP] mediamtx unavailable — using Socket.IO fallback.")

    # ── Async tasks ───────────────────────────────────────────────────────────
    task_weight = asyncio.create_task(weight_worker(active_event, weight_q))
    task_main   = asyncio.create_task(main_item_detection(active_event, weight_q, yolo_q))

    # Flask (local video + API endpoints)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Relay to Admin (Socket.IO + RTSP frame push)
    relay_thread = threading.Thread(
        target=relay_worker, args=(active_event, relay_q), daemon=True
    )
    relay_thread.start()

    # ── NEW: Raw camera TCP relay to Admin over Tailscale ─────────────────────
    cam_relay_thread = threading.Thread(
        target=raw_cam_relay_worker, args=(raw_cam_q,), daemon=True
    )
    cam_relay_thread.start()
    print("[CAM-TCP] Raw camera relay thread started.")

    try:
        await asyncio.gather(task_weight, task_main)
    finally:
        task_weight.cancel()
        task_main.cancel()
        print("[STOP] Closing processes...")
        active_event.clear()
        stop_evt.set()

        for p in (p_capture, p_infer_a, p_infer_b, p_infer_c, p_ui):
            if p.is_alive():
                p.join(timeout=1)
                if p.is_alive():
                    p.terminate()

        # Cleanup RTSP subprocesses
        for proc in (_ffmpeg_proc, _mediamtx_proc):
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass

        try:
            shm.close()
            shm.unlink()
        except Exception:
            pass
        print("[OK] All processes stopped")

if __name__ == "__main__":
    mp.freeze_support()  # Fix PyInstaller multiprocessing infinite popup issue
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[STOP] Stopped by User")