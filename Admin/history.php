<?php
session_start();
if (empty($_SESSION['Admin_id'])) {
    header('Location: login.php');
    exit;
}

require 'includes/db.php';
require 'includes/header.php';

// Time range filter (1, 3, 6, or 12 months)
$months = isset($_GET['months']) ? (int)$_GET['months'] : 3;
if ($months <= 0) $months = 3;

// Compute starting date
$start = date('Y-m-d 00:00:00', strtotime("-{$months} months"));

// Aggregate by type for date range
$stmt = $pdo->prepare("
    SELECT 
        i.type AS type,
        COUNT(*) AS quantity,
        (SUM(r.weight) / 1000) AS weight,
        SEC_TO_TIME(AVG(TIME_TO_SEC(TIME(r.recycle_date)))) AS avg_time,
        MIN(r.recycle_date) AS start_date,
        MAX(r.recycle_date) AS end_date
    FROM recycle r
    JOIN item_types i ON r.item_type_id = i.item_id
    WHERE r.recycle_date BETWEEN ? AND NOW()
    GROUP BY i.type
    ORDER BY quantity DESC
");
$stmt->execute([$start]);

$rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>
<main class="admin-main">
  <h1 class="admin-title">History Report</h1>
  <p class="admin-subtitle">Filter recycling totals by time range and export as PDF.</p>

  <div class="toolbar">
    <form method="get" class="toolbar-left" style="align-items:center;">
      <label style="color:rgba(255,255,255,.85);font-weight:800;">
        Show last
        <select class="select" name="months" onchange="this.form.submit()" style="display:inline-block;max-width:180px;margin-left:8px;">
          <option value="1" <?= $months===1?'selected':'' ?>>1 month</option>
          <option value="3" <?= $months===3?'selected':'' ?>>3 months</option>
          <option value="6" <?= $months===6?'selected':'' ?>>6 months</option>
          <option value="12" <?= $months===12?'selected':'' ?>>12 months</option>
        </select>
      </label>
    </form>

    <div class="toolbar-right">
      <a class="btn btn-secondary" href="generate_pdf.php?months=<?= $months ?>">Generate PDF</a>
    </div>
  </div>

  <div class="admin-card">
    <div class="admin-card-header">Totals by Type</div>
    <div class="admin-card-body" style="padding:0;">
      <table class="table">
        <thead>
          <tr>
            <th>Type</th>
            <th>Quantity</th>
            <th>Weight (kg)</th>
            <th>Submit Date Range</th>
          </tr>
        </thead>
        <tbody>
          <?php if (!$rows): ?>
            <tr><td colspan="5" class="text-center">No data for the selected range.</td></tr>
          <?php else: ?>
            <?php foreach($rows as $r): ?>
              <tr>
                <td><strong><?= htmlspecialchars($r['type']) ?></strong></td>
                <td><?= (int)$r['quantity'] ?></td>
                <td><?= htmlspecialchars(number_format($r['weight'],2)) ?></td>
                <td><?= htmlspecialchars($r['start_date'] . ' - ' . $r['end_date']) ?></td>
              </tr>
            <?php endforeach; ?>

            <?php
              $totalQty = array_sum(array_column($rows, 'quantity'));
              $totalWeight = array_sum(array_column($rows, 'weight'));
            ?>
            <tr>
              <td><strong>Total</strong></td>
              <td><strong><?= (int)$totalQty ?></strong></td>
              <td><strong><?= htmlspecialchars(number_format($totalWeight,2)) ?></strong></td>
              <td>—</td>
              <td>—</td>
            </tr>
          <?php endif; ?>
        </tbody>
      </table>
    </div>
  </div>
</main>

<?php require 'includes/footer.php'; ?>
