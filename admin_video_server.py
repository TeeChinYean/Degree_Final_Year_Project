"""
admin_video_server.py  — Admin Video Relay Server
- Listens for station registrations via Socket.IO
- PRIMARY: Tries to pull RTSP stream from each station (cv2.VideoCapture)
- FALLBACK: If RTSP fails, accepts Base64 JPEG frames via Socket.IO 'video_frame' event
- Broadcasts all frames to Admin browser (live_view.php) as 'video_frame_broadcast'
- Forwards admin_command to target station

── NEW ──────────────────────────────────────────────────────────────────────────
- Raw Camera TCP Listener (port 55200):
    Accepts a persistent TCP connection from each station's raw_cam_relay_worker.
    The station sends raw (no-overlay) MJPEG frames so the admin can see the
    physical camera view even when detection is inactive.
    Frames are served as an MJPEG HTTP stream at:
        GET /raw_cam/<site_id>
    and also broadcast via Socket.IO event 'raw_cam_frame' for live_view.php.
─────────────────────────────────────────────────────────────────────────────────
"""

import threading
import time
import base64
import requests
import struct
import json

import cv2
from flask import Flask, request, jsonify, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS

import os
import socket as _socket

# ── Config ────────────────────────────────────────────────────────────────────
PHP_SITE_URL      = os.environ.get('PHP_SITE_URL', 'http://localhost')
PHP_API_URL       = f"{PHP_SITE_URL}/Front-end/api_station.php"
RTSP_TIMEOUT_SEC  = 8
RTSP_RECONNECT_SEC = 15
OFFLINE_MARK_SEC   = 10

# ── NEW: Raw camera TCP config ────────────────────────────────────────────────
CAM_STREAM_PORT   = int(os.environ.get('CAM_STREAM_PORT', 55200))
# Max frames kept in memory per station for MJPEG HTTP streaming
CAM_FRAME_BUFFER  = 1   # We only need the latest frame


# ── Flask + SocketIO ──────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=10,
    ping_interval=5
)

# ── State ─────────────────────────────────────────────────────────────────────
site_registry: dict[str, dict] = {}
registry_lock = threading.Lock()

# ── NEW: Raw cam state ────────────────────────────────────────────────────────
# site_id -> latest raw JPEG bytes (no overlay, straight from camera)
raw_cam_frames: dict[str, bytes] = {}
raw_cam_lock  = threading.Lock()


# ─────────────────────────────────────────────────────────────────────────────
# ── NEW: Raw Camera TCP Listener ──────────────────────────────────────────────
#
# Protocol (mirrors tailscale_pc_*.py length-prefix pattern):
#   Handshake  ← station sends  4-byte len  +  JSON {"type":"cam_register","site_id":"...","station_ip":"..."}
#   Per frame  ← station sends  4-byte len  +  raw JPEG bytes  (continuous push)
#
# One thread per connected station is spawned by the accept loop.
# ─────────────────────────────────────────────────────────────────────────────

def _recv_exactly_tcp(sock: _socket.socket, n: int) -> bytes | None:
    """Read exactly n bytes from a socket. Returns None on disconnect."""
    buf = b""
    while len(buf) < n:
        try:
            chunk = sock.recv(n - len(buf))
        except Exception:
            return None
        if not chunk:
            return None
        buf += chunk
    return buf


def _handle_cam_station(conn: _socket.socket, addr):
    """
    Handle one station's raw camera TCP connection.
    Reads continuous JPEG frames and stores the latest in raw_cam_frames.
    Also broadcasts each frame via Socket.IO so the browser gets it in real time.
    """
    site_id    = None
    station_ip = addr[0]

    try:
        # ── Handshake ────────────────────────────────────────────────────────
        raw_len = _recv_exactly_tcp(conn, 4)
        if not raw_len:
            return
        (length,) = struct.unpack(">I", raw_len)
        raw_body = _recv_exactly_tcp(conn, length)
        if not raw_body:
            return

        try:
            meta = json.loads(raw_body.decode("utf-8"))
        except Exception:
            return

        if meta.get("type") != "cam_register":
            return

        site_id    = meta.get("site_id", addr[0])
        station_ip = meta.get("station_ip", addr[0])
        print(f"[CAM-TCP] Station '{site_id}' ({station_ip}) connected for raw camera stream.")

        # ── Frame receive loop ────────────────────────────────────────────────
        while True:
            # Read 4-byte frame length
            raw_len = _recv_exactly_tcp(conn, 4)
            if not raw_len:
                break
            (frame_len,) = struct.unpack(">I", raw_len)

            # Sanity-check: reject obviously wrong sizes (>5 MB)
            if frame_len == 0 or frame_len > 5 * 1024 * 1024:
                break

            # Read JPEG bytes
            jpeg_bytes = _recv_exactly_tcp(conn, frame_len)
            if not jpeg_bytes:
                break

            # Store latest frame
            with raw_cam_lock:
                raw_cam_frames[site_id] = jpeg_bytes

            # Broadcast to browser via Socket.IO (base64 so JSON-safe)
            b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
            socketio.emit('raw_cam_frame', {
                'site_id':    site_id,
                'station_ip': station_ip,
                'image':      b64,
            })

    except Exception as e:
        print(f"[CAM-TCP] Error for station '{site_id}': {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass
        if site_id:
            with raw_cam_lock:
                raw_cam_frames.pop(site_id, None)
            print(f"[CAM-TCP] Station '{site_id}' disconnected from raw camera stream.")


def cam_tcp_listener():
    """
    Accept-loop: listens on CAM_STREAM_PORT for incoming station TCP connections.
    Each accepted connection gets its own daemon thread.
    """
    srv = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    srv.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", CAM_STREAM_PORT))
    srv.listen(10)
    srv.settimeout(1.0)
    print(f"[CAM-TCP] Listening for raw camera connections on port {CAM_STREAM_PORT}")

    while True:
        try:
            conn, addr = srv.accept()
        except _socket.timeout:
            continue
        except Exception as e:
            print(f"[CAM-TCP] Accept error: {e}")
            continue

        t = threading.Thread(
            target=_handle_cam_station,
            args=(conn, addr),
            daemon=True
        )
        t.start()


# ── NEW: MJPEG HTTP endpoint — admin browser can open this as an <img src="..."> ──
@app.route('/raw_cam/<site_id>')
def raw_cam_stream(site_id: str):
    """
    Serve the raw (no-overlay) camera feed for a specific station as MJPEG.
    Usage in admin PHP:  <img src="http://localhost:5001/raw_cam/SITE_ABC">
    """
    def generate():
        while True:
            with raw_cam_lock:
                jpeg = raw_cam_frames.get(site_id)

            if jpeg:
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n'
                    + jpeg
                    + b'\r\n'
                )
            else:
                # Send a tiny keep-alive gap if no frame yet
                time.sleep(0.1)
                continue

            time.sleep(1 / 15)   # ~15 fps to browser

    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# ── NEW: List which stations have an active raw cam stream ────────────────────
@app.route('/api/raw_cam_stations', methods=['GET'])
def api_raw_cam_stations():
    """Return list of stations currently streaming raw camera."""
    with raw_cam_lock:
        return jsonify(list(raw_cam_frames.keys()))


# ─────────────────────────────────────────────────────────────────────────────
# RTSP Pull Worker — runs in a daemon thread per station
# ─────────────────────────────────────────────────────────────────────────────
def rtsp_pull_worker(site_id: str, rtsp_url: str):
    """Pull frames from RTSP and broadcast to admin browser."""
    print(f"[RTSP] Starting pull for {site_id}: {rtsp_url}")
    failure_count = 0

    while True:
        with registry_lock:
            info = site_registry.get(site_id)
            if info is None:
                print(f"[RTSP] {site_id} removed from registry, stopping pull.")
                return
            if not info.get('use_rtsp', True):
                print(f"[RTSP] {site_id} switched to Socket.IO fallback, stopping RTSP pull.")
                return

        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            failure_count += 1
            print(f"[RTSP] {site_id} — cannot open stream (attempt {failure_count}).")
            if failure_count >= 1:
                with registry_lock:
                    if site_id in site_registry:
                        site_registry[site_id]['use_rtsp'] = False
                print(f"[RTSP] {site_id} — switching to Socket.IO fallback.")
                return
            time.sleep(RTSP_RECONNECT_SEC)
            continue


        failure_count = 0
        print(f"[RTSP] {site_id} — stream opened successfully.")

        while True:
            ok, frame = cap.read()
            if not ok:
                print(f"[RTSP] {site_id} — frame read failed, reconnecting...")
                with registry_lock:
                    if site_id in site_registry:
                        site_registry[site_id]['rtsp_has_frames'] = False
                break

            with registry_lock:
                if site_id in site_registry:
                    site_registry[site_id]['rtsp_has_frames'] = True


            # Resize to reduce bandwidth to browser
            h, w = frame.shape[:2]
            frame_small = cv2.resize(frame, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
            ok2, buf = cv2.imencode('.jpg', frame_small, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            if not ok2:
                continue

            b64 = base64.b64encode(buf).decode('utf-8')
            with registry_lock:
                info = site_registry.get(site_id, {})
                station_ip = info.get('ip', '')

            socketio.emit('video_frame_broadcast', {
                'site_id':    site_id,
                'station_ip': station_ip,
                'image':      b64,
                'source':     'rtsp'
            })

            with registry_lock:
                if site_id in site_registry:
                    site_registry[site_id]['last_seen'] = time.time()

            time.sleep(1 / 20)  # ~20 fps cap to browser

        cap.release()
        time.sleep(2)  # Brief pause before reconnect


# ─────────────────────────────────────────────────────────────────────────────
# Offline monitor — marks stations offline if silent too long
# ─────────────────────────────────────────────────────────────────────────────
def offline_monitor():
    while True:
        time.sleep(5)
        now = time.time()
        offline_sites = []
        with registry_lock:
            for site_id, info in site_registry.items():
                last = info.get('last_seen', now)
                if now - last > OFFLINE_MARK_SEC:
                    offline_sites.append(site_id)
                    socketio.emit('station_offline', {'site_id': site_id})
        # Mark offline in DB via PHP heartbeat
        for site_id in offline_sites:
            try:
                requests.post(PHP_API_URL + '?action=offline', json={
                    'site_id': site_id
                }, timeout=3)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# Socket.IO event handlers
# ─────────────────────────────────────────────────────────────────────────────
@socketio.on('connect')
def handle_connect():
    print(f"[SOCKET] Client connected: {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    print(f"[SOCKET] Client disconnected: {request.sid}")
    with registry_lock:
        for site_id, info in list(site_registry.items()):
            if info.get('sid') == request.sid:
                site_registry[site_id]['is_socket_connected'] = False
                print(f"[SOCKET] Station {site_id} socket disconnected.")


@socketio.on('register_site')
def handle_register(data):
    """
    Called by main_system.exe on startup.
    data = { 'site_id': str, 'station_ip': str, 'rtsp_port': int }
    """
    site_id    = data.get('site_id', '')
    station_ip = data.get('station_ip', request.environ.get('REMOTE_ADDR', ''))
    rtsp_port  = int(data.get('rtsp_port', 8554))

    if not site_id:
        return

    rtsp_url = f"rtsp://{station_ip}:{rtsp_port}/live"
    print(f"[REG] Station registered: {site_id} | IP={station_ip} | RTSP={rtsp_url}")

    with registry_lock:
        site_registry[site_id] = {
            'sid':               request.sid,
            'ip':                station_ip,
            'rtsp_port':         rtsp_port,
            'use_rtsp':          True,
            'rtsp_has_frames':   False,
            'last_seen':         time.time(),
            'is_socket_connected': True,
        }

    # Notify browser: new station online
    emit('station_online', {
        'site_id':    site_id,
        'station_ip': station_ip,
    }, broadcast=True)

    # Update DB via PHP API (heartbeat)
    try:
        requests.post(PHP_API_URL + "?action=heartbeat", json={
            'site_id':    site_id,
            'station_ip': station_ip,
        }, timeout=3)
    except Exception as e:
        print(f"[REG] DB heartbeat failed: {e}")

    # Start RTSP pull thread
    t = threading.Thread(
        target=rtsp_pull_worker,
        args=(site_id, rtsp_url),
        daemon=True
    )
    t.start()
    with registry_lock:
        if site_id in site_registry:
            site_registry[site_id]['rtsp_thread'] = t


@socketio.on('video_frame')
def handle_video_frame(data):
    """
    Socket.IO FALLBACK — broadcast if RTSP is NOT active or not yet delivering frames.
    data = { 'site_id': str, 'image': base64_jpeg }
    """
    site_id = data.get('site_id', '')
    with registry_lock:
        info = site_registry.get(site_id, {})
        use_rtsp  = info.get('use_rtsp', True)
        rtsp_has_frames = info.get('rtsp_has_frames', False)
        station_ip = info.get('ip', '')

    if use_rtsp and rtsp_has_frames:
        return

    # Fallback path
    data['station_ip'] = station_ip
    data['source']     = 'socketio'
    emit('video_frame_broadcast', data, broadcast=True)

    with registry_lock:
        if site_id in site_registry:
            site_registry[site_id]['last_seen'] = time.time()


@socketio.on('admin_command')
def handle_admin_command(data):
    """Forward enable/disable command from admin browser to target station."""
    site_id = data.get('site_id')
    action  = data.get('action')
    with registry_lock:
        info = site_registry.get(site_id, {})
        sid  = info.get('sid')

    if sid:
        print(f"[CMD] Admin → {site_id}: {action}")
        emit('control_command', {'action': action}, to=sid)
    else:
        print(f"[CMD] {site_id} not connected.")


# ─────────────────────────────────────────────────────────────────────────────
# HTTP API  — for admin PHP pages to query live station list
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/stations', methods=['GET'])
def api_stations():
    """Return list of currently connected stations."""
    with registry_lock:
        result = [
            {
                'site_id':    sid,
                'station_ip': info.get('ip', ''),
                'use_rtsp':   info.get('use_rtsp', True),
                'last_seen':  info.get('last_seen', 0),
                'online':     (time.time() - info.get('last_seen', 0)) < OFFLINE_MARK_SEC,
            }
            for sid, info in site_registry.items()
        ]
    return jsonify(result)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Start offline monitor thread
    monitor_thread = threading.Thread(target=offline_monitor, daemon=True)
    monitor_thread.start()

    # ── NEW: Start raw camera TCP listener ────────────────────────────────────
    cam_listener_thread = threading.Thread(target=cam_tcp_listener, daemon=True)
    cam_listener_thread.start()

    print("=" * 60)
    print("  Admin Video Relay Server  —  Port 5001")
    print(f"  PHP API: {PHP_API_URL}")
    print(f"  (Set env PHP_SITE_URL to override, e.g. http://100.111.777.94)")
    print("  RTSP pull primary / Socket.IO fallback enabled")
    print(f"  Raw Camera TCP listener: port {CAM_STREAM_PORT}")
    print(f"  Raw cam MJPEG endpoint:  /raw_cam/<site_id>")
    print("=" * 60)
    socketio.run(app, host='0.0.0.0', port=5001)