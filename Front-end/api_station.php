<?php
/**
 * api_station.php  — Station management REST API
 */
session_start();
require './config.php';

// Always return JSON — suppress PHP HTML error output
ini_set('display_errors', 0);
header('Content-Type: application/json');

// Global exception handler: ensure JSON even on fatal DB errors
set_exception_handler(function(Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
    exit;
});

$action = $_GET['action'] ?? ($_POST['action'] ?? '');

// ── Helper ───────────────────────────────────────────────────────────────────
function json_out($data, int $code = 200): void {
    http_response_code($code);
    echo json_encode($data);
    exit;
}

function require_admin(): void {
    if (empty($_SESSION['Admin_id'])) {
        json_out(['error' => 'Unauthorized'], 403);
    }
}

// ── GET: list stations (admin) ────────────────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'GET' && $action === 'list') {
    require_admin();
    global $pdo;
    $stmt = $pdo->query('SELECT * FROM stations ORDER BY applied_at DESC');
    json_out($stmt->fetchAll());
}

// ── POST: station applies for registration (called by setup.py) ───────────────
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $action === 'apply') {
    $body  = json_decode(file_get_contents('php://input'), true) ?? [];
    $sid   = trim($body['site_id']    ?? '');
    $name  = trim($body['station_name'] ?? '');
    $ip    = trim($body['station_ip'] ?? $_SERVER['REMOTE_ADDR']);
    $port  = (int)($body['rtsp_port'] ?? 8554);

    if (!$sid || !$name) {
        json_out(['error' => 'site_id and station_name are required'], 400);
    }

    global $pdo;

    // Check if already exists
    $check = $pdo->prepare('SELECT status FROM stations WHERE site_id = ?');
    $check->execute([$sid]);
    $existing = $check->fetch();

    if ($existing) {
        // Re-apply: update IP and reset to pending if rejected; keep approved
        if ($existing['status'] === 'rejected') {
            $pdo->prepare(
                'UPDATE stations SET station_name=?, station_ip=?, rtsp_port=?, status="pending", applied_at=NOW() WHERE site_id=?'
            )->execute([$name, $ip, $port, $sid]);
            json_out(['status' => 'reapplied', 'site_id' => $sid]);
        }
        json_out(['status' => $existing['status'], 'site_id' => $sid]);
    }

    $pdo->prepare(
        'INSERT INTO stations (site_id, station_name, station_ip, rtsp_port, status, applied_at)
         VALUES (?, ?, ?, ?, "pending", NOW())'
    )->execute([$sid, $name, $ip, $port]);

    json_out(['status' => 'pending', 'site_id' => $sid], 201);
}

// ── POST: station heartbeat / update IP (called by main_system.exe via socketio, proxied here) ──
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $action === 'heartbeat') {
    $body  = json_decode(file_get_contents('php://input'), true) ?? [];
    $sid   = trim($body['site_id']    ?? '');
    $ip    = trim($body['station_ip'] ?? '');
    if (!$sid) json_out(['error' => 'site_id required'], 400);

    global $pdo;
    $pdo->prepare(
        'UPDATE stations SET station_ip=COALESCE(NULLIF(?,\"\"),station_ip), last_seen=NOW(), is_online=1 WHERE site_id=?'
    )->execute([$ip, $sid]);
    json_out(['ok' => true]);
}

// ── POST: admin approves / rejects a station ──────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $action === 'approve') {
    require_admin();
    $body   = json_decode(file_get_contents('php://input'), true) ?? [];
    $sid    = trim($body['site_id'] ?? '');
    $result = $body['result'] ?? 'approved'; // 'approved' | 'rejected'

    if (!$sid || !in_array($result, ['approved', 'rejected'])) {
        json_out(['error' => 'Invalid params'], 400);
    }

    global $pdo;
    $pdo->prepare(
        'UPDATE stations SET status=?, approved_at=? WHERE site_id=?'
    )->execute([$result, $result === 'approved' ? date('Y-m-d H:i:s') : null, $sid]);
    json_out(['ok' => true, 'site_id' => $sid, 'status' => $result]);
}

// ── POST: admin assigns / unassigns user to station ─────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $action === 'assign_user') {
    require_admin();
    $body       = json_decode(file_get_contents('php://input'), true) ?? [];
    $user_id    = (int)($body['user_id'] ?? 0);
    $station_id = $body['station_id'] ?? null; // null = unassign

    if (!$user_id) json_out(['error' => 'user_id required'], 400);

    global $pdo;
    if ($station_id) {
        // UPSERT: insert or update the user_station row
        $pdo->prepare(
            'INSERT INTO user_station (user_id, station_id) VALUES (?, ?)
             ON DUPLICATE KEY UPDATE station_id = VALUES(station_id)'
        )->execute([$user_id, $station_id]);
    } else {
        // Remove assignment
        $pdo->prepare('DELETE FROM user_station WHERE user_id = ?')
            ->execute([$user_id]);
    }
    json_out(['ok' => true]);
}

// ── GET: check own station status (called by setup.py polling) ───────────────
if ($_SERVER['REQUEST_METHOD'] === 'GET' && $action === 'status') {
    $sid = trim($_GET['site_id'] ?? '');
    if (!$sid) json_out(['error' => 'site_id required'], 400);

    global $pdo;
    $stmt = $pdo->prepare('SELECT status, station_name FROM stations WHERE site_id=?');
    $stmt->execute([$sid]);
    $row = $stmt->fetch();
    if (!$row) json_out(['error' => 'not found'], 404);
    json_out(['status' => $row['status'], 'station_name' => $row['station_name']]);
}

// ── GET: get station info for current logged-in user (called by dashboard/camera) ──
if ($_SERVER['REQUEST_METHOD'] === 'GET' && $action === 'my_station') {
    if (!isset($_SESSION['user_id'])) json_out(['assigned' => false]);

    global $pdo;
    try {
        $stmt = $pdo->prepare(
            'SELECT s.site_id, s.station_name, s.station_ip, s.rtsp_port, s.status, s.is_online
             FROM user_station us
             JOIN stations s ON us.station_id = s.site_id
             WHERE us.user_id = ?'
        );
        $stmt->execute([$_SESSION['user_id']]);
        $row = $stmt->fetch();
        if (!$row) json_out(['assigned' => false]);
        json_out(array_merge(['assigned' => true], $row));
    } catch (Exception $e) {
        // Table not yet created or other DB error — treat as not assigned
        json_out(['assigned' => false, '_note' => $e->getMessage()]);
    }
}

json_out(['error' => 'Unknown action'], 400);
