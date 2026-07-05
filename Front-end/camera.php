<?php
session_start();
require './config.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: ./login.php');
    exit;
}

// ── Fetch this user's assigned station from DB ────────────────────────────
$station = null;
$stmt = $pdo->prepare(
    'SELECT s.site_id, s.station_name, s.station_ip, s.status, s.is_online
     FROM user_station us
     JOIN stations s ON us.station_id = s.site_id
     WHERE us.user_id = ?'
);
$stmt->execute([$_SESSION['user_id']]);
$station = $stmt->fetch();

// Station not assigned or not approved
$station_ok   = $station && $station['site_id'] && $station['status'] === 'approved';
$station_ip   = $station_ok ? $station['station_ip'] : '';
$station_name = $station_ok ? htmlspecialchars($station['station_name']) : '';

include './header.php';
?>

<main class="wrap container">
    <div class="page-header">
        <h1>AI Detection Camera</h1>
        <p class="page-subtitle">Position items in front of the camera for automatic detection</p>
    </div>

<?php if (!$station_ok): ?>
    <!-- ── No station assigned ─────────────────────────────────────────── -->
    <div style="
        background:rgba(255,193,7,.12);border:1px solid #ffc107;
        border-radius:12px;padding:2rem;text-align:center;margin:2rem auto;max-width:480px;">
        <div style="font-size:2.5rem;margin-bottom:.75rem;">📡</div>
        <h3 style="margin:0 0 .5rem;">No Station Assigned</h3>
        <p style="color:#aaa;margin:0 0 1.2rem;">
            Your account is not linked to an approved recycling station.<br>
            Please contact the admin to assign you to a station.
        </p>
        <a href="./dashboard.php" class="btn btn-outline btn-block" style="display:inline-block;">← Back to Dashboard</a>
    </div>
<?php else: ?>
    <!-- ── Camera permission + stream ────────────────────────────────── -->

    <!-- Camera permission overlay -->
    <div id="cam-permission-overlay" style="
        display:none;position:fixed;inset:0;background:rgba(0,0,0,.65);
        z-index:9999;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:1rem;">
        <div style="background:#1e1e2e;border-radius:16px;padding:2.5rem 3rem;text-align:center;max-width:380px;box-shadow:0 8px 40px rgba(0,0,0,.5);">
            <div style="font-size:3rem;margin-bottom:1rem;">📷</div>
            <h3 style="margin:0 0 .5rem;color:#fff;">Camera Access Required</h3>
            <p style="color:#aaa;margin:0 0 1.5rem;font-size:.9rem;">
                Station <strong style="color:#69d3c5;"><?= $station_name ?></strong> needs to
                verify your camera is available before starting detection.
            </p>
            <button id="allow-cam-btn" class="btn btn-primary btn-block" style="width:100%;">
                Allow Camera &amp; Continue
            </button>
            <a href="./dashboard.php" style="display:block;margin-top:.75rem;color:#666;font-size:.85rem;">Cancel</a>
        </div>
    </div>

    <div class="detection-grid" id="detection-grid" style="display:none;">

        <div class="stream-box">
            <div class="stream-actions" style="margin-bottom: 12px; display: flex; justify-content: center; gap: 10px;">
                <button type="button" id="btn-relay" class="btn btn-primary" style="padding: 4px 12px; font-size: 0.85rem;">🌐 Relay (Socket.IO)</button>
                <button type="button" id="btn-webrtc" class="btn btn-outline" style="padding: 4px 12px; font-size: 0.85rem;">⚡ WebRTC (Direct)</button>
                <button type="button" id="btn-mjpeg" class="btn btn-outline" style="padding: 4px 12px; font-size: 0.85rem;">📹 MJPEG (Direct)</button>
            </div>
            <div class="video-container">
                <!-- Primary Relay stream image -->
                <img id="relay-stream"
                     src=""
                     alt="Relay Stream"
                     class="video-feed"
                     style="width:100%; aspect-ratio:4/3; border-radius:12px; object-fit:contain; background:#000;">
                <!-- WebRTC/RTSP player from mediamtx -->
                <iframe id="webrtc-stream"
                        src="http://<?= $station_ip ?>:8889/camera"
                        frameborder="0"
                        scrolling="no"
                        allow="autoplay"
                        style="display:none; width:100%; aspect-ratio:4/3; border-radius:12px; background:#000;">
                </iframe>
                <!-- Fallback direct MJPEG stream -->
                <img id="video"
                     src="http://<?= $station_ip ?>:5000/video"
                     alt="Detection Stream"
                     class="video-feed"
                     style="display:none; width:100%; aspect-ratio:4/3; border-radius:12px; object-fit:contain; background:#000;">
            </div>
            <div style="margin-top:.5rem;font-size:.8rem;color:#888;text-align:center;">
                Station: <strong style="color:#69d3c5;"><?= $station_name ?></strong>
                &nbsp;|&nbsp; Tailscale IP: <code><?= htmlspecialchars($station_ip) ?></code>
                &nbsp;|&nbsp; RTSP Stream: <code>rtsp://<?= htmlspecialchars($station_ip) ?>:8554/camera</code>
            </div>
        </div>

        <div class="results-sidebar">
            <div class="sidebar-header">
                <h3>Live Detection</h3>
            </div>

            <div class="result-list">
                <div class="result-placeholder">
                    <div id="result" aria-live="polite" aria-relevant="additions"></div>
                </div>
            </div>

            <div class="sidebar-actions">
                <button type="button" id="confirmBtn" class="btn btn-primary btn-block">
                    ✓ Confirm Submission
                </button>
                <a href="./dashboard.php" id="backBtn" class="btn btn-outline btn-block">
                    ← Return to Dashboard
                </a>
            </div>
        </div>
    </div>
<?php endif; ?>
</main>

<?php if ($station_ok): ?>
<script src="https://cdn.socket.io/4.6.0/socket.io.min.js"></script>
<script>
// ── Station info from PHP ──────────────────────────────────────────────────
const STATION_IP   = <?= json_encode($station_ip) ?>;
const STATION_BASE = `http://${STATION_IP}:5000`;
const SITE_ID      = <?= json_encode($station['site_id']) ?>;

// ── Socket.IO Relay Connection ─────────────────────────────────────────────
const protocol   = window.location.protocol;
const SERVER_IP  = window.location.hostname;
let SOCKET_URL   = `${protocol}//${SERVER_IP}:5001`;

if (SERVER_IP.includes('cloudflare.com')) {
    SOCKET_URL = `http://100.111.777.94:5001`;
}

const socket = io(SOCKET_URL, {
    reconnectionDelay: 1000,
    transports: ['polling', 'websocket']
});

socket.on('connect', () => {
    console.log('[SOCKET] Connected to relay server:', SOCKET_URL);
});

socket.on('video_frame_broadcast', (data) => {
    if (data.site_id === SITE_ID) {
        const relayImg = document.getElementById('relay-stream');
        if (relayImg) {
            relayImg.src = 'data:image/jpeg;base64,' + data.image;
        }
    }
});

// ── 1) Camera permission check (MediaStream API) ───────────────────────────
// Shows an overlay asking the user to allow camera access.
// This confirms the station's physical camera is available in the browser context.
// We do NOT capture or display the browser stream — it's released immediately.
(function checkCameraPermission() {
    const overlay = document.getElementById('cam-permission-overlay');
    const grid    = document.getElementById('detection-grid');
    const btn     = document.getElementById('allow-cam-btn');

    // Check if permission already granted
    navigator.permissions && navigator.permissions.query({ name: 'camera' })
        .then(result => {
            if (result.state === 'granted') {
                // Already have permission — skip overlay
                grid.style.display = '';
                startSSE();
                return;
            }
            overlay.style.display = 'flex';
        })
        .catch(() => {
            // permissions API not available — show overlay anyway
            overlay.style.display = 'flex';
        });

    btn.addEventListener('click', async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            // Permission granted — release the stream immediately (we don't need it)
            stream.getTracks().forEach(t => t.stop());
            overlay.style.display = 'none';
            grid.style.display = '';
            startSSE();
        } catch (err) {
            alert(
                'Camera permission denied or not available.\n\n' +
                'The station camera feed will still display below, but please ensure ' +
                'the physical camera at station "' + <?= json_encode($station_name) ?> + '" is connected.'
            );
            overlay.style.display = 'none';
            grid.style.display = '';
            startSSE();
        }
    });
})();

// ── 2) Detection results container ─────────────────────────────────────────
const resultContainer = document.getElementById("result");
let detectionResults = [];

// Clear any leftover data from previous session immediately on page load.
// This ensures SSE always starts fresh from index 0 — no duplicates possible.
fetch(`${STATION_BASE}/clear_data`, { method: "POST" }).catch(() => {});

// ── 3) Page unload: deactivate + clear ────────────────────────────────────
window.addEventListener("beforeunload", function () {
    fetch(`${STATION_BASE}/clear_data`,  { method: "POST", keepalive: true });
    fetch(`${STATION_BASE}/activate`, {
        method: "POST", keepalive: true,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: false })
    });
});

// ── 4) SSE real-time detection & Stream Toggle ─────────────────────────────
let sseStarted = false;
function startSSE() {
    if (sseStarted) return;
    sseStarted = true;
    
    // Activate AI detection on station
    fetch(`${STATION_BASE}/activate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: true })
    })
    .then(async res => {
        const d = await res.json();
        if (!res.ok || d.status === 'disabled') {
            alert("⚠️ This station has been temporarily disabled by the Admin.");
            window.location.href = "./dashboard.php";
        }
    })
    .catch(err => console.error("Activation error", err));

    // Continuous heartbeat check: If admin disables site while user is on camera page, kick them out
    setInterval(() => {
        fetch(`${STATION_BASE}/system_status`)
            .then(res => res.json())
            .then(data => {
                if (data && data.admin_enabled === false) {
                    alert("⚠️ This station has just been disabled by the Admin.");
                    window.location.href = "./dashboard.php";
                }
            })
            .catch(() => {});
    }, 3000);

    // Stream Toggle Logic
    const relayImg    = document.getElementById('relay-stream');
    const webrtcFrame = document.getElementById('webrtc-stream');
    const mjpegImg    = document.getElementById('video');
    const btnRelay    = document.getElementById('btn-relay');
    const btnWebrtc   = document.getElementById('btn-webrtc');
    const btnMjpeg    = document.getElementById('btn-mjpeg');

    function switchStream(mode) {
        if (mode === 'relay') {
            relayImg.style.display    = 'block';
            webrtcFrame.style.display = 'none';
            mjpegImg.style.display    = 'none';
            btnRelay.className        = 'btn btn-primary';
            btnWebrtc.className       = 'btn btn-outline';
            btnMjpeg.className        = 'btn btn-outline';
        } else if (mode === 'webrtc') {
            relayImg.style.display    = 'none';
            webrtcFrame.style.display = 'block';
            mjpegImg.style.display    = 'none';
            btnRelay.className        = 'btn btn-outline';
            btnWebrtc.className       = 'btn btn-primary';
            btnMjpeg.className        = 'btn btn-outline';
        } else {
            relayImg.style.display    = 'none';
            webrtcFrame.style.display = 'none';
            mjpegImg.style.display    = 'block';
            btnRelay.className        = 'btn btn-outline';
            btnWebrtc.className       = 'btn btn-outline';
            btnMjpeg.className        = 'btn btn-primary';
        }
    }

    // Default to MJPEG direct (clearest — goes straight from station to browser)
    switchStream('mjpeg');

    btnRelay.addEventListener('click', () => switchStream('relay'));
    btnWebrtc.addEventListener('click', () => switchStream('webrtc'));
    btnMjpeg.addEventListener('click', () => switchStream('mjpeg'));

    // SSE always starts from 0 — data_list was cleared on page load above.
    const evtSource = new EventSource(`${STATION_BASE}/word_event?from=0`);

    // If the network blips (e.g. VPN), EventSource automatically reconnects.
    // Because it re-requests ?from=0, the server will replay the entire list.
    // We clear the client UI on connection open so the replay perfectly syncs without duplicates.
    evtSource.onopen = function() {
        detectionResults = [];
        resultContainer.innerHTML = "";
    };

    evtSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        detectionResults.push(data);

        const p = document.createElement("p");
        p.innerText = `${data.item} - ${data.weight} g`;
        p.style.color   = "white";
        p.style.border  = "1px solid white";
        p.style.padding = "10px";
        resultContainer.appendChild(p);

        if (resultContainer.children.length > 20)
            resultContainer.removeChild(resultContainer.firstChild);

        resultContainer.scrollTop = resultContainer.scrollHeight;
    };

    evtSource.onerror = function(err) {
        console.error("SSE error", err);
    };
}

// ── 5) Confirm button ──────────────────────────────────────────────────────
document.getElementById("confirmBtn").addEventListener("click", function(e) {
    e.preventDefault();

    if (detectionResults.length === 0) {
        alert("No items detected.");
        return;
    }

    fetch('process_detection.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(detectionResults)
    })
    .then(res => {
        if (!res.ok) throw new Error("Submit failed");
        return fetch(`${STATION_BASE}/clear_data`, { method: "POST" });
    })
    .then(() => {
        resultContainer.innerHTML = "";
        detectionResults = [];
        window.location.href = 'detection_result.php';
    })
    .catch(err => alert(err.message));
});

// ── 6) Back button ─────────────────────────────────────────────────────────
document.getElementById("backBtn").addEventListener("click", async function(e) {
    const btn = e.currentTarget;
    if (btn.disabled) return;
    e.preventDefault();
    btn.disabled = true;
    btn.innerText = "Processing...";
    try {
        await Promise.all([
            fetch(`${STATION_BASE}/clear_data`, { method: "POST" }),
            fetch(`${STATION_BASE}/activate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ active: false })
            })
        ]);
    } catch (error) {
        console.error("Request failed", error);
    } finally {
        window.location.href = "./dashboard.php";
    }
});
</script>
<?php endif; ?>

<?php include './footer.php'; ?>
