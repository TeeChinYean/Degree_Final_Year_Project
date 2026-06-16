<?php
/**
 * Admin/manage_stations.php  — Station Management Dashboard
 */
session_start();
ini_set('display_errors', 0);
error_reporting(0);
if (empty($_SESSION['Admin_id'])) {
    header('Location: ./login.php');
    exit;
}

// Load DB via shared admin config
require_once './includes/db.php';


// Fetch all stations
$stations = $pdo->query('SELECT * FROM stations ORDER BY applied_at DESC')->fetchAll();

// Check if the user_station relation table exists
$hasRelTable = false;
try {
    $pdo->query("SELECT 1 FROM user_station LIMIT 1");
    $hasRelTable = true;
} catch (Exception $e) {}

// Fetch all users + their assigned station (via user_station relation table)
if ($hasRelTable) {
    $users = $pdo->query(
        'SELECT u.User_id, u.User_name, u.User_email,
                us.station_id, us.connected_at, s.station_name
         FROM users u
         LEFT JOIN user_station us ON u.User_id = us.user_id
         LEFT JOIN stations s     ON us.station_id = s.site_id
         ORDER BY u.User_name'
    )->fetchAll();
} else {
    // Relation table not yet created — show users without station info
    $users = $pdo->query(
        'SELECT User_id, User_name, User_email,
                NULL AS station_id, NULL AS station_name
         FROM users ORDER BY User_name'
    )->fetchAll();
}

// Approved stations for user-assignment dropdown
$approved_stations = $pdo->query(
    "SELECT site_id, station_name, station_ip FROM stations WHERE status='approved' ORDER BY station_name"
)->fetchAll();


?>
<?php require_once './includes/header.php'; ?>

<!-- Bootstrap + station page styles -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
  .main-content { padding: 1.5rem 2rem; }
  .card { border: none; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,.08); margin-bottom: 1.5rem; }
  .badge-pending  { background:#ffc107 !important; color:#333 !important; }
  .badge-approved { background:#198754 !important; }
  .badge-rejected { background:#dc3545 !important; }
  .status-dot { width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px; }
  .dot-online { background:#22c55e; }
  .dot-offline{ background:#6b7280; }
  .section-title { font-size:1.1rem;font-weight:700;color:#1a1a2e;margin-bottom:1rem; }
  th { font-size:.82rem;text-transform:uppercase;letter-spacing:.5px;color:#6b7280; }
  td { vertical-align:middle;font-size:.9rem; }
  .action-btn { font-size:.8rem;padding:4px 10px; }
</style>

<div class="main-content">

<div class="container-fluid px-4">

  <!-- ── Alert area ─────────────────────────────────────────────────────── -->
  <div id="alertBox" class="alert d-none" role="alert"></div>

  <!-- ── Station Applications ───────────────────────────────────────────── -->
  <div class="card mb-4 p-4">
    <div class="section-title">📡 Station Applications</div>
    <?php if (empty($stations)): ?>
      <p class="text-muted">No station applications yet.</p>
    <?php else: ?>
    <div class="table-responsive">
      <table class="table table-hover align-middle">
        <thead>
          <tr>
            <th>Site ID</th>
            <th>Name</th>
            <th>IP Address</th>
            <th>Applied</th>
            <th>Status</th>
            <th>Online</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
        <?php foreach ($stations as $s): ?>
          <tr id="row-<?= htmlspecialchars($s['site_id']) ?>">
            <td><code><?= htmlspecialchars($s['site_id']) ?></code></td>
            <td><?= htmlspecialchars($s['station_name']) ?></td>
            <td><?= htmlspecialchars($s['station_ip']) ?></td>
            <td><?= $s['applied_at'] ? date('M d H:i', strtotime($s['applied_at'])) : '—' ?></td>
            <td>
              <span class="badge badge-<?= $s['status'] ?> rounded-pill" id="status-<?= htmlspecialchars($s['site_id']) ?>">
                <?= ucfirst($s['status']) ?>
              </span>
            </td>
            <td>
              <span class="status-dot <?= $s['is_online'] ? 'dot-online' : 'dot-offline' ?>"></span>
              <?= $s['is_online'] ? 'Online' : 'Offline' ?>
            </td>
            <td>
              <?php if ($s['status'] === 'pending'): ?>
              <button class="btn btn-success action-btn me-1"
                onclick="approveStation('<?= htmlspecialchars($s['site_id']) ?>', 'approved')">
                ✔ Approve
              </button>
              <button class="btn btn-danger action-btn"
                onclick="approveStation('<?= htmlspecialchars($s['site_id']) ?>', 'rejected')">
                ✗ Reject
              </button>
              <?php elseif ($s['status'] === 'approved'): ?>
              <button class="btn btn-warning action-btn"
                onclick="approveStation('<?= htmlspecialchars($s['site_id']) ?>', 'rejected')">
                Revoke
              </button>
              <?php elseif ($s['status'] === 'rejected'): ?>
              <button class="btn btn-outline-success action-btn"
                onclick="approveStation('<?= htmlspecialchars($s['site_id']) ?>', 'approved')">
                Re-approve
              </button>
              <?php endif; ?>
            </td>
          </tr>
        <?php endforeach; ?>
        </tbody>
      </table>
    </div>
    <?php endif; ?>
  </div>

  <!-- ── User → Active Connections ─────────────────────────────────────── -->
  <div class="card p-4">
    <div class="section-title">👤 Active User Connections </div>
    <?php if (empty($users)): ?>
      <p class="text-muted">No users found.</p>
    <?php else: ?>
    <div class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>User ID</th>
            <th>Username</th>
            <th>Email</th>
            <th>Current Station</th>
            <th>Connected Time</th>
          </tr>
        </thead>
        <tbody>
        <?php foreach ($users as $u): ?>
          <tr>
            <td><?= (int)$u['User_id'] ?></td>
            <td><?= htmlspecialchars($u['User_name']) ?></td>
            <td><?= htmlspecialchars($u['User_email'] ?? '') ?></td>
            <td>
              <?= $u['station_id']
                    ? '<span class="badge bg-primary">' . htmlspecialchars($u['station_name'] ?: $u['station_id']) . '</span>'
                    : '<span class="text-muted">None</span>' ?>
            </td>
            <td>
              <span class="text-muted">
                <?= !empty($u['connected_at']) ? htmlspecialchars($u['connected_at']) : '—' ?>
              </span>
            </td>
          </tr>
        <?php endforeach; ?>
        </tbody>
      </table>
    </div>
    <?php endif; ?>
  </div>

</div><!-- /main-content -->

<script>
const API = '../Front-end/api_station.php';

function showAlert(msg, type = 'success') {
  const box = document.getElementById('alertBox');
  box.className = `alert alert-${type}`;
  box.textContent = msg;
  box.classList.remove('d-none');
  setTimeout(() => box.classList.add('d-none'), 4000);
}

async function approveStation(siteId, result) {
  const label = result === 'approved' ? 'Approve' : (result === 'rejected' ? 'Reject' : 'Revoke');
  if (!confirm(`${label} station "${siteId}"?`)) return;

  const resp = await fetch(API + '?action=approve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ site_id: siteId, result })
  });
  const data = await resp.json();
  if (data.ok) {
    showAlert(`Station ${siteId} ${result}.`);
    // Update badge in table
    const badge = document.getElementById('status-' + siteId);
    if (badge) {
      badge.className = `badge badge-${result} rounded-pill`;
      badge.textContent = result.charAt(0).toUpperCase() + result.slice(1);
    }
  } else {
    showAlert('Error: ' + (data.error || 'unknown'), 'danger');
  }
}

async function assignUser(userId) {
  const sel = document.getElementById('sel-' + userId);
  const stationId = sel.value || null;

  const resp = await fetch(API + '?action=assign_user', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, station_id: stationId })
  });
  const data = await resp.json();
  if (data.ok) {
    showAlert('User assignment saved.');
  } else {
    showAlert('Error: ' + (data.error || 'unknown'), 'danger');
  }
}
</script>

<?php require_once './includes/footer.php'; ?>
