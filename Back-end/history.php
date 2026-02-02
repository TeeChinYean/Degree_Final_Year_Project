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
$start = date('Y-m-d', strtotime("-{$months} months"));

// Aggregate by type for date range
$stmt = $pdo->prepare("
    SELECT 
        i.Type AS type,
        SUM(r.count) AS quantity,
        SUM(r.weight) AS weight,
        MIN(r.recycle_date) AS start_date,
        MAX(r.recycle_date) AS end_date
    FROM recycle r
    JOIN item_types i ON r.item_type_id = i.item_id
    WHERE r.recycle_date BETWEEN ? AND CURDATE()
    GROUP BY i.Type
    ORDER BY quantity DESC
");
$stmt->execute([$start]);

$rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
?>
<main style="max-width:1100px;margin:36px auto;padding:20px">
  <h2 style="background:#0f5b63;color:#fff;padding:12px 14px;border-radius:6px;text-align:center">
    Recycling History Report
  </h2>

  <div style="display:flex;justify-content:space-between;align-items:center;margin:12px 0">
    <!-- Time Range Dropdown -->
    <form method="get" style="display:inline-block">
      <label>Show last
        <select name="months" onchange="this.form.submit()" style="padding:6px;border-radius:6px;border:1px solid #ccc">
          <option value="1" <?= $months===1?'selected':'' ?>>1 month</option>
          <option value="3" <?= $months===3?'selected':'' ?>>3 months</option>
          <option value="6" <?= $months===6?'selected':'' ?>>6 months</option>
          <option value="12" <?= $months===12?'selected':'' ?>>12 months</option>
        </select>
      </label>
    </form>

    <!-- Generate PDF Button -->
    <div>
      <a href="generate_pdf.php?months=<?= $months ?>" 
         style="background:#50c8c0;color:#fff;padding:8px 10px;border-radius:6px;text-decoration:none">
        Generate Report (PDF)
      </a>
    </div>
  </div>

  <!-- Data Table -->
  <table style="width:100%;border-collapse:collapse;margin-top:10px">
    <thead style="background:#eef4ff;text-align:left">
      <tr>
        <th style="padding:10px;border-bottom:1px solid #ddd">Type</th>
        <th style="padding:10px;border-bottom:1px solid #ddd">Quantity</th>
        <th style="padding:10px;border-bottom:1px solid #ddd">Weight (kg)</th>
        <th style="padding:10px;border-bottom:1px solid #ddd">Average Submit Time</th>
        <th style="padding:10px;border-bottom:1px solid #ddd">Submit Date Range</th>
      </tr>
    </thead>
    <tbody>
      <?php if (!$rows): ?>
        <tr><td colspan="5" style="padding:14px;text-align:center">No data for the selected range.</td></tr>
      <?php else: ?>
        <?php foreach($rows as $r): ?>
          <tr>
            <td style="padding:10px"><?= htmlspecialchars($r['type']) ?></td>
            <td style="padding:10px"><?= (int)$r['quantity'] ?></td>
            <td style="padding:10px"><?= htmlspecialchars(number_format($r['weight'],2)) ?></td>
            <td style="padding:10px"><?= htmlspecialchars($r['avg_time'] ?: '—') ?></td>
            <td style="padding:10px"><?= htmlspecialchars($r['start_date'] . ' - ' . $r['end_date']) ?></td>
          </tr>
        <?php endforeach; ?>

        <?php
          // Add total row
          $totalQty = array_sum(array_column($rows, 'quantity'));
          $totalWeight = array_sum(array_column($rows, 'weight'));
        ?>
        <tr style="font-weight:bold;background:#f9f9f9">
          <td style="padding:10px">Total</td>
          <td style="padding:10px"><?= (int)$totalQty ?></td>
          <td style="padding:10px"><?= htmlspecialchars(number_format($totalWeight,2)) ?></td>
          <td style="padding:10px">—</td>
          <td style="padding:10px">—</td>
        </tr>
      <?php endif; ?>
    </tbody>
  </table>
</main>

<?php require 'includes/footer.php'; ?>
