<?php
require './config.php';
session_start();
if(!isset($_SESSION['user_id'])) header('Location: ./login.php');

$user_id = $_SESSION['user_id'];
$stmt = $pdo->prepare('SELECT User_name, balance FROM users WHERE User_id=?');
$stmt->execute([$user_id]);
$user = $stmt->fetch();

// ── Auto-bind connecting user to current station ────────────────────────────
try {
    $remoteIp = $_SERVER['REMOTE_ADDR'];
    $stmtSt = $pdo->prepare('SELECT site_id FROM stations WHERE station_ip = ? AND status="approved" LIMIT 1');
    $stmtSt->execute([$remoteIp]);
    $stRow = $stmtSt->fetch();

    if ($stRow) {
        $pdo->prepare('INSERT INTO user_station (user_id, station_id, connected_at) VALUES (?, ?, NOW()) ON DUPLICATE KEY UPDATE station_id=VALUES(station_id), connected_at=NOW()')->execute([$user_id, $stRow['site_id']]);
    } else {
        $stmtStAny = $pdo->query('SELECT site_id FROM stations WHERE status="approved" ORDER BY is_online DESC, last_seen DESC LIMIT 1');
        $anySt = $stmtStAny->fetch();
        if ($anySt) {
            $pdo->prepare('INSERT INTO user_station (user_id, station_id, connected_at) VALUES (?, ?, NOW()) ON DUPLICATE KEY UPDATE station_id=VALUES(station_id), connected_at=NOW()')->execute([$user_id, $anySt['site_id']]);
        }
    }
} catch (Exception $e) {}

include './header.php';
?>

<main class="wrap container">
    <div class="dashboard-header">
        <div class="dashboard-welcome">
            <h1>Welcome back, <?= htmlspecialchars($user['User_name']); ?>!</h1>
            <p class="dashboard-subtitle">Track your recycling progress and manage your rewards</p>
        </div>
        
        <div class="dashboard-stats">
            <div class="stat-card stat-primary">
                <div class="stat-icon">🌱</div>
                <div class="stat-content">
                    <div class="stat-value"><?= (int)$user['balance']; ?></div>
                    <div class="stat-label">Green Points</div>
                </div>
            </div>
        </div>
    </div>

    <div class="dashboard-actions">
        <form method="post" action="start_detect_setup.php" style="margin: 0; display: inline-block;">
            <button class="btn btn-primary btn-large" name="start_detection" type="submit">
                🎯 Start New Detection
            </button>
        </form>
        <a href="./items.php" class="btn btn-outline btn-large">
            📋 View Item Types
        </a>
    </div>

    <section class="info-card dashboard-section">
        <div class="section-header">
            <h2>Recent Recycling Activity</h2>
            <p class="section-subtitle">Your latest recycling submissions</p>
        </div>
        
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Material Type</th>
                        <th>Weight</th>
                        <th>Points Earned</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    <?php
                    $s = $pdo->prepare('
                        SELECT r.item_type_id, i.type, r.weight, i.points, r.recycle_date
                        FROM recycle r
                        JOIN item_types i ON r.item_type_id = i.item_id
                        WHERE r.user_id = ?
                        ORDER BY r.recycle_date DESC
                        LIMIT 10
                    ');
                    $s->execute([$user_id]);
                    $rows = $s->fetchAll();

                    if (!$rows): ?>
                        <tr>
                            <td colspan="4" class="empty-state">
                                <div class="empty-icon">♻️</div>
                                <p><strong>No recycling activity yet.</strong></p>
                                <p class="empty-hint">Start detecting items to earn your first Green Points!</p>
                            </td>
                        </tr>
                    <?php else: 
                        foreach ($rows as $r): ?>
                             <tr>
                                <td><strong><?= htmlspecialchars($r['type']); ?></strong></td>
                                <td><?= number_format((float)$r['weight'], 1); ?>g</td>
                                <td><span class="points-badge">+<?= (int)$r['points']; ?></span></td>
                                <td><?= date('M d, Y', strtotime($r['recycle_date'])); ?></td>
                            </tr>
                        <?php endforeach; 
                    endif; ?>
                </tbody>
            </table>
        </div>
    </section>

    <section class="info-card dashboard-section">
        <div class="section-header">
            <h2>Your Recycling Chart</h2>
            <p class="section-subtitle">See how much you’ve recycled in the last 6 months.</p>
        </div>

        <div id="recycleChartEmpty" class="empty-state" style="display:none;">
            <div class="empty-icon">📈</div>
            <p><strong>No chart data yet.</strong></p>
            <p class="empty-hint">Recycle your first item to start tracking progress!</p>
        </div>

        <div id="recycleCharts" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;align-items:stretch;">
            <div class="info-card" style="margin:0;">
                <div class="section-header" style="margin-bottom:10px;">
                    <h2 style="font-size:1.25rem;margin:0;">Total Weight by Type</h2>
                    <p class="section-subtitle" style="margin:6px 0 0;">Sum of weights (grams)</p>
                </div>
                <canvas id="userWeightPie" height="220"></canvas>
            </div>

            <div class="info-card" style="margin:0;">
                <div class="section-header" style="margin-bottom:10px;">
                    <h2 style="font-size:1.25rem;margin:0;">Monthly Total Weight</h2>
                    <p class="section-subtitle" style="margin:6px 0 0;">All materials combined</p>
                </div>
                <canvas id="userMonthlyLine" height="220"></canvas>
            </div>
        </div>
    </section>
</main>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
async function fetchUserRecycleData() {
  const resp = await fetch('./user_chart_data.php', { cache: 'no-store' });
  return await resp.json();
}

(async () => {
  const data = await fetchUserRecycleData();
  if (data && data.error) return;

  const types = data.types || [];
  const totalsWeight = data.totalsWeight || {};
  const months = data.months || [];
  const monthlyWeight = data.monthlyWeight || {};

  const anyWeight = types.some(t => (totalsWeight[t] || 0) > 0);
  if (!anyWeight && months.every(m => (monthlyWeight[m] || 0) <= 0)) {
    document.getElementById('recycleCharts').style.display = 'none';
    document.getElementById('recycleChartEmpty').style.display = 'block';
    return;
  }

  // Doughnut chart: weight by type
  const pieData = types.map(t => totalsWeight[t] || 0);
  new Chart(document.getElementById('userWeightPie'), {
    type: 'doughnut',
    data: {
      labels: types,
      datasets: [{
        data: pieData,
        backgroundColor: ['#69d3c5','#6ac1ff','#3b82c4','#ffb86b','#7f6cf5','#4ade80','#f97316','#22c55e']
      }]
    },
    options: {
      plugins: { legend: { position: 'bottom' } }
    }
  });

  // Line chart: monthly total weight
  const series = months.map(m => monthlyWeight[m] || 0);
  new Chart(document.getElementById('userMonthlyLine'), {
    type: 'line',
    data: {
      labels: months,
      datasets: [{
        label: 'Total weight (g)',
        data: series,
        fill: true,
        tension: 0.3,
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34,197,94,0.18)',
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: '#fff'
      }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true } },
      plugins: { legend: { position: 'bottom' } }
    }
  });
})();
</script>

<?php include './footer.php'; ?>
