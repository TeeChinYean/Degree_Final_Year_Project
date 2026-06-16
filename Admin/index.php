<?php
require 'includes/db.php';
session_start();

if (empty($_SESSION['Admin_id'])) {
    header('Location: login.php');
    exit;
}

// --- Fetch totals grouped by item type ---
$stmt = $pdo->query("
    SELECT 
        i.type AS Type,
        COUNT(*)           AS total_recycle,
        SUM(r.weight)      AS total_weight,
        AVG(r.weight)      AS avg_weight
    FROM recycle r
    LEFT JOIN item_types i ON r.Item_type_id = i.item_id
    GROUP BY r.Item_type_id, i.type
    ORDER BY total_recycle DESC
");
$rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>
<?php require 'includes/header.php'; ?>

<main class="admin-main" role="main">
  <h1 class="admin-title">Monthly Report</h1>
  <p class="admin-subtitle">Overview of recycling submissions and average weights.</p>

  <div class="admin-card" style="margin-top:16px;">
    <div class="admin-card-header">Report Table</div>
    <div class="admin-card-body">
      <table class="table">
      <thead>
        <tr>
          <th>Item Type</th>
          <th>Total Recycle</th>
          <th>Total Weight (g)</th>
          <th>Average Weight (g)</th>
        </tr>
      </thead>
      <tbody>
        <?php if (empty($rows)): ?>
        <tr>
          <td colspan="4" style="text-align:center; padding:24px; opacity:0.7;">No recycling data yet.</td>
        </tr>
        <?php else: ?>
        <?php foreach($rows as $r): ?>
        <tr>
          <td><?= htmlspecialchars($r['Type'] ?? 'Unknown') ?></td>
          <td><span class="pill pill--ok"><?= (int)$r['total_recycle'] ?></span></td>
          <td><?= number_format((float)$r['total_weight'], 2) ?></td>
          <td><?= number_format((float)$r['avg_weight'], 2) ?></td>
        </tr>
        <?php endforeach; ?>
        <?php endif; ?>
      </tbody>
      </table>
    </div>
  </div>
</main>

<!-- No AJAX update, since recycle table has no quantity/status -->
<?php require 'includes/footer.php'; ?>
