<?php
session_start();
if (empty($_SESSION['Admin_id'])) {
    header('Location: ./login.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Live Monitor — Green Point Admin</title>
<script src="https://cdn.socket.io/4.6.0/socket.io.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
/* ── Reset & Base ─────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --bg:          #080c14;
    --bg-panel:    #0d1220;
    --bg-card:     #111827;
    --bg-card2:    #1a2235;
    --border:      rgba(255,255,255,.06);
    --border-glow: rgba(34,197,94,.35);
    --accent:      #22c55e;
    --accent2:     #3b82f6;
    --accent3:     #f59e0b;
    --danger:      #ef4444;
    --text:        #e2e8f0;
    --text-muted:  #64748b;
    --text-dim:    #94a3b8;
    --glow-green:  0 0 20px rgba(34,197,94,.25);
    --glow-blue:   0 0 20px rgba(59,130,246,.25);
    --radius:      12px;
    --radius-sm:   8px;
}

body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
}

/* ── Top Bar ──────────────────────────────────────────────────────────── */
.topbar {
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(8,12,20,.92);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.5rem;
    height: 56px;
}

.topbar-left { display: flex; align-items: center; gap: 1rem; }

.brand {
    display: flex;
    align-items: center;
    gap: .6rem;
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: -.01em;
    color: #fff;
    text-decoration: none;
}

.brand-dot {
    width: 32px; height: 32px;
    border-radius: 8px;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    display: flex; align-items: center; justify-content: center;
    font-size: .9rem;
    box-shadow: var(--glow-green);
}

.back-btn {
    display: flex;
    align-items: center;
    gap: .4rem;
    font-size: .8rem;
    color: var(--text-muted);
    text-decoration: none;
    padding: .35rem .75rem;
    border-radius: 6px;
    border: 1px solid var(--border);
    transition: all .2s;
}
.back-btn:hover { color: var(--text); border-color: rgba(255,255,255,.15); }

.topbar-right { display: flex; align-items: center; gap: 1rem; }

.conn-badge {
    display: flex;
    align-items: center;
    gap: .5rem;
    font-size: .78rem;
    font-weight: 500;
    padding: .3rem .75rem;
    border-radius: 20px;
    border: 1px solid var(--border);
    transition: all .4s;
}
.conn-badge.connected {
    border-color: rgba(34,197,94,.4);
    background: rgba(34,197,94,.08);
    color: #4ade80;
}
.conn-badge.disconnected {
    border-color: rgba(239,68,68,.4);
    background: rgba(239,68,68,.08);
    color: #f87171;
}

.conn-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: currentColor;
}
.conn-badge.connected .conn-dot {
    animation: pulse-green 2s infinite;
}
@keyframes pulse-green {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:.5; transform:scale(.8); }
}

.stat-bar {
    display: flex;
    gap: 1.5rem;
    font-size: .78rem;
}
.stat-item { color: var(--text-muted); }
.stat-item span { color: var(--text); font-weight: 600; }

/* ── Main Layout ──────────────────────────────────────────────────────── */
.main {
    padding: 1.25rem 1.5rem;
    min-height: calc(100vh - 56px);
}

/* ── Empty State ──────────────────────────────────────────────────────── */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    min-height: 60vh;
    color: var(--text-muted);
}
.empty-icon {
    width: 80px; height: 80px;
    border-radius: 50%;
    background: rgba(255,255,255,.04);
    border: 1px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem;
}
.empty-state h3 { color: var(--text-dim); font-weight: 600; }
.empty-state p  { font-size: .9rem; text-align: center; max-width: 320px; }

/* ── Video Grid ───────────────────────────────────────────────────────── */
.video-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 1.25rem;
}

/* ── Station Card ─────────────────────────────────────────────────────── */
.station-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: border-color .3s, box-shadow .3s;
}
.station-card.live {
    border-color: rgba(34,197,94,.25);
    box-shadow: 0 0 0 1px rgba(34,197,94,.1), 0 8px 32px rgba(0,0,0,.4);
}
.station-card.offline {
    border-color: var(--border);
    opacity: .75;
}

/* Card Header */
.card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: .75rem 1rem;
    background: var(--bg-card2);
    border-bottom: 1px solid var(--border);
    gap: .5rem;
}

.card-head-left { flex: 1; min-width: 0; }

.station-name {
    font-size: .92rem;
    font-weight: 600;
    color: #fff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.station-meta {
    display: flex;
    align-items: center;
    gap: .6rem;
    margin-top: 3px;
}

.station-ip {
    font-family: 'JetBrains Mono', monospace;
    font-size: .7rem;
    color: #60a5fa;
    background: rgba(59,130,246,.1);
    padding: 1px 6px;
    border-radius: 4px;
}

.source-tag {
    font-size: .65rem;
    font-weight: 600;
    letter-spacing: .5px;
    padding: 1px 5px;
    border-radius: 3px;
    text-transform: uppercase;
}
.source-tag.rtsp     { background:rgba(34,197,94,.15); color:#4ade80; }
.source-tag.socketio { background:rgba(245,158,11,.15); color:#fbbf24; }

.card-head-right { display:flex; align-items:center; gap:.5rem; flex-shrink:0; }

.status-pill {
    font-size: .7rem;
    font-weight: 700;
    letter-spacing: .5px;
    padding: 3px 9px;
    border-radius: 20px;
    text-transform: uppercase;
}
.status-pill.live    { background:rgba(34,197,94,.2); color:#4ade80; border:1px solid rgba(34,197,94,.3); }
.status-pill.offline { background:rgba(100,116,139,.15); color:#94a3b8; border:1px solid rgba(100,116,139,.2); }

.live-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 6px #22c55e;
    animation: blink 1.5s infinite;
    display: none;
}
.station-card.live .live-dot { display: block; }

@keyframes blink {
    0%,100% { opacity:1; } 50% { opacity:.3; }
}

/* Video Area */
.video-area {
    position: relative;
    aspect-ratio: 4/3;
    background: #000;
    overflow: hidden;
}

.video-area img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
}

.video-area img.hidden { display: none; }

.no-signal {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: .6rem;
    background: repeating-linear-gradient(
        45deg,
        rgba(255,255,255,.01) 0px,
        rgba(255,255,255,.01) 1px,
        transparent 1px,
        transparent 8px
    );
}
.no-signal-icon { font-size: 2.5rem; opacity: .3; }
.no-signal-text {
    font-size: .8rem;
    font-weight: 600;
    letter-spacing: 2px;
    color: var(--text-muted);
    text-transform: uppercase;
}
.no-signal.hidden { display: none; }

/* Scanline overlay */
.scanline {
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
        to bottom,
        transparent 0px,
        transparent 3px,
        rgba(0,0,0,.08) 3px,
        rgba(0,0,0,.08) 4px
    );
    pointer-events: none;
    opacity: .4;
}

/* FPS counter overlay */
.fps-overlay {
    position: absolute;
    top: 8px;
    right: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: .65rem;
    color: #22c55e;
    background: rgba(0,0,0,.6);
    padding: 2px 6px;
    border-radius: 4px;
    letter-spacing: .3px;
    pointer-events: none;
}

/* Card Footer */
.card-foot {
    display: flex;
    gap: .5rem;
    padding: .65rem 1rem;
    border-top: 1px solid var(--border);
    background: var(--bg-card2);
}

.cmd-btn {
    flex: 1;
    padding: .4rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: transparent;
    color: var(--text-dim);
    font-size: .78rem;
    font-weight: 500;
    cursor: pointer;
    transition: all .2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: .3rem;
}
.cmd-btn.enable:hover  { border-color:rgba(34,197,94,.5); color:#4ade80; background:rgba(34,197,94,.08); }
.cmd-btn.disable:hover { border-color:rgba(239,68,68,.5);  color:#f87171; background:rgba(239,68,68,.08);  }

/* ── Scrollbar ─────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,.1); border-radius: 3px; }
</style>
</head>
<body>

<!-- ── Top Bar ────────────────────────────────────────────────────────── -->
<header class="topbar">
    <div class="topbar-left">
        <a class="brand" href="index.php">
            <div class="brand-dot">🌿</div>
            <span>Green Point</span>
        </a>
        <a class="back-btn" href="index.php">← Admin</a>
    </div>

    <div class="topbar-right">
        <div class="stat-bar">
            <div class="stat-item">Sites Live: <span id="count-live">0</span></div>
            <div class="stat-item">Total: <span id="count-total">0</span></div>
        </div>
        <div class="conn-badge disconnected" id="conn-badge">
            <div class="conn-dot"></div>
            <span id="conn-text">Connecting…</span>
        </div>
    </div>
</header>

<!-- ── Main ───────────────────────────────────────────────────────────── -->
<main class="main">

    <!-- Empty state shown until first station connects -->
    <div class="empty-state" id="empty-state">
        <div class="empty-icon">📡</div>
        <h3>No Stations Connected</h3>
        <p>Waiting for station feeds. Make sure <code>admin_video_server.py</code> is running and stations are online.</p>
    </div>

    <div class="video-grid" id="video-grid"></div>

</main>

<script>
// ── Config ────────────────────────────────────────────────────────────────
const protocol   = window.location.protocol;
const SERVER_IP  = window.location.hostname;
let SOCKET_URL   = `${protocol}//${SERVER_IP}:5001`;

// Cloudflare tunnels do not forward port 5001. Fallback to admin server's Tailscale IP.
if (SERVER_IP.includes('cloudflare.com')) {
    SOCKET_URL = `http://100.111.777.94:5001`;
}

// ── State ─────────────────────────────────────────────────────────────────
const socket      = io(SOCKET_URL, { 
    reconnectionDelay: 1000,
    transports: ['polling', 'websocket']
});
const activeSites = {};          // safeId → { lastSeen, frameCount, startTime }
const OFFLINE_MS  = 4000;

// ── UI refs ───────────────────────────────────────────────────────────────
const connBadge  = document.getElementById('conn-badge');
const connText   = document.getElementById('conn-text');
const countLive  = document.getElementById('count-live');
const countTotal = document.getElementById('count-total');
const emptyState = document.getElementById('empty-state');
const videoGrid  = document.getElementById('video-grid');

// ── Socket events ─────────────────────────────────────────────────────────
socket.on('connect', () => {
    connBadge.className = 'conn-badge connected';
    connText.innerText  = 'Connected';
    console.log('[SOCKET] Connected to relay server:', SOCKET_URL);
});

socket.on('connect_error', (err) => {
    connBadge.className = 'conn-badge disconnected';
    connText.innerText  = 'Conn Error';
    console.error('[SOCKET] Connect error to ' + SOCKET_URL + ':', err);
    if (window.location.protocol === 'https:' && SOCKET_URL.startsWith('http://')) {
        emptyState.innerHTML = `
            <div class="empty-icon" style="color: #f59e0b;">🔒</div>
            <h3 style="color: #f59e0b;">Browser Blocked Video Stream (Mixed Content)</h3>
            <p style="max-width: 480px; text-align: left; background: rgba(245,158,11,0.1); padding: 1rem; border-radius: 8px; border: 1px solid rgba(245,158,11,0.3);">
                You are accessing via Cloudflare HTTPS, but the video relay server is on HTTP (<code>100.111.777.94:5001</code>).<br><br>
                <b>To view live video in Chrome / Edge:</b><br>
                1. Click the lock icon 🔒 next to the URL address bar above.<br>
                2. Click <b>Site Settings</b>.<br>
                3. Find <b>Insecure Content</b> (不安全内容) and change it to <b>Allow</b> (允许).<br>
                4. Reload this page.
            </p>
        `;
        emptyState.style.display = 'flex';
    }
});


socket.on('disconnect', () => {
    connBadge.className = 'conn-badge disconnected';
    connText.innerText  = 'Disconnected';
});


socket.on('video_frame_broadcast', (data) => {
    const siteId    = data.site_id    || 'Unknown';
    const stationIp = data.station_ip || '—';
    const imgSrc    = 'data:image/jpeg;base64,' + data.image;
    const source    = data.source     || 'socketio';
    const safeId    = 'site-' + siteId.replace(/\W/g, '_');

    // Hide empty state
    emptyState.style.display = 'none';

    if (!document.getElementById(safeId)) {
        createCard(safeId, siteId, stationIp, source, imgSrc);
        activeSites[safeId] = { lastSeen: Date.now(), frameCount: 1, startTime: Date.now() };
        updateCounts();
    } else {
        updateCard(safeId, imgSrc, source);
        activeSites[safeId].lastSeen = Date.now();
        activeSites[safeId].frameCount++;
    }
});

socket.on('station_offline', (data) => {
    const safeId = 'site-' + (data.site_id || '').replace(/\W/g, '_');
    markOffline(safeId);
});

// ── Card creation ─────────────────────────────────────────────────────────
function createCard(safeId, siteId, ip, source, imgSrc) {
    const card = document.createElement('div');
    card.className = 'station-card live';
    card.id = safeId;
    card.innerHTML = `
        <div class="card-head">
            <div class="card-head-left">
                <div class="station-name">📹 ${escHtml(siteId)}</div>
                <div class="station-meta">
                    <span class="station-ip">${escHtml(ip)}</span>
                    <span class="source-tag ${source}" id="src-${safeId}">${source.toUpperCase()}</span>
                </div>
            </div>
            <div class="card-head-right">
                <div class="live-dot"></div>
                <span class="status-pill live" id="status-${safeId}">LIVE</span>
            </div>
        </div>
        <div class="video-area">
            <img id="img-${safeId}" src="${imgSrc}" alt="${escHtml(siteId)} feed">
            <div class="no-signal hidden" id="nosig-${safeId}">
                <div class="no-signal-icon">📵</div>
                <div class="no-signal-text">No Signal</div>
            </div>
            <div class="scanline"></div>
            <div class="fps-overlay" id="fps-${safeId}">— fps</div>
        </div>
        <div class="card-foot">
            <button class="cmd-btn enable"  onclick="sendCommand('${escHtml(siteId)}','enable')">
                ✔ Enable
            </button>
            <button class="cmd-btn disable" onclick="sendCommand('${escHtml(siteId)}','disable')">
                ✖ Disable
            </button>
        </div>
    `;
    videoGrid.appendChild(card);
}

// ── Card update ───────────────────────────────────────────────────────────
function updateCard(safeId, imgSrc, source) {
    const img    = document.getElementById('img-'    + safeId);
    const nosig  = document.getElementById('nosig-'  + safeId);
    const status = document.getElementById('status-' + safeId);
    const srcEl  = document.getElementById('src-'    + safeId);
    const card   = document.getElementById(safeId);

    if (img)    img.src = imgSrc;
    if (srcEl)  { srcEl.textContent = source.toUpperCase(); srcEl.className = `source-tag ${source}`; }

    // Restore live state
    if (img && img.classList.contains('hidden')) {
        img.classList.remove('hidden');
        if (nosig)  nosig.classList.add('hidden');
        if (status) { status.className = 'status-pill live'; status.textContent = 'LIVE'; }
        if (card)   { card.className = 'station-card live'; }
    }
}

// ── Mark offline ──────────────────────────────────────────────────────────
function markOffline(safeId) {
    const img    = document.getElementById('img-'    + safeId);
    const nosig  = document.getElementById('nosig-'  + safeId);
    const status = document.getElementById('status-' + safeId);
    const card   = document.getElementById(safeId);

    if (img && !img.classList.contains('hidden')) {
        img.classList.add('hidden');
        if (nosig)  nosig.classList.remove('hidden');
        if (status) { status.className = 'status-pill offline'; status.textContent = 'OFFLINE'; }
        if (card)   card.className = 'station-card offline';
    }
    updateCounts();
}

// ── FPS calculator ────────────────────────────────────────────────────────
setInterval(() => {
    const now = Date.now();
    let live = 0;

    for (const [safeId, info] of Object.entries(activeSites)) {
        if (now - info.lastSeen > OFFLINE_MS) {
            markOffline(safeId);
        } else {
            live++;
            // Estimate fps from frame count over uptime (rough)
            const upSec = (now - info.startTime) / 1000;
            const fps   = upSec > 0 ? (info.frameCount / upSec).toFixed(1) : '—';
            const fpsEl = document.getElementById('fps-' + safeId);
            if (fpsEl) fpsEl.textContent = `${fps} fps`;
        }
    }

    countLive.textContent  = live;
    countTotal.textContent = Object.keys(activeSites).length;
}, 1000);

// ── Commands ──────────────────────────────────────────────────────────────
function sendCommand(siteId, action) {
    socket.emit('admin_command', { site_id: siteId, action });
    console.log(`[CMD] ${action} → ${siteId}`);
}

// ── Helpers ───────────────────────────────────────────────────────────────
function escHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function updateCounts() {
    const total  = Object.keys(activeSites).length;
    const live   = document.querySelectorAll('.station-card.live').length;
    countLive.textContent  = live;
    countTotal.textContent = total;
}
</script>

</body>
</html>
