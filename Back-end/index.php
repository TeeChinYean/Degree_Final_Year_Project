<?php
require 'includes/db.php';
session_start();

// --- Fetch all data for table display with item type ---
$stmt = $pdo->query("
    SELECT r.Recycle_Id, r.User_id, r.Item_type_id, r.weight, r.Recycle_Date, i.Type
    FROM recycle r
    LEFT JOIN item_types i ON r.Item_type_id = i.Item_Id
    ORDER BY r.weight ASC
");
$rows = $stmt->fetchAll(PDO::FETCH_ASSOC);

// --- Compute average weight ---
$total = array_sum(array_column($rows, 'weight'));
$count = count($rows);
$average = $count > 0 ? $total / $count : 0;
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GreenPoint — Monthly Report</title>
<link rel="stylesheet" href="./style/backend.css">
<style>
body {font-family:Arial,sans-serif;background:#f6f8fa;margin:0;}
.container {max-width:1100px;margin:40px auto;background:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.1);}
.card-header {font-size:22px;font-weight:bold;color:#0f5b63;margin-bottom:20px;text-align:center;}
.table-wrap {overflow-x:auto;}
table {width:100%;border-collapse:collapse;}
th, td {padding:10px 8px;border-bottom:1px solid #ddd;text-align:left;}
th {background:#e0f7f4;color:#0f5b63;}
td input {padding:6px;border:1px solid #ccc;border-radius:4px;width:100%;}
.footer {text-align:center;padding:12px 0;color:#666;font-size:14px;}
tr[data-id]:hover {background:#f9f9f9;}
.success {background:#e8ffe8 !important;transition:background 0.3s;}
</style>
</head>

<body>
<?php include 'includes/header.php'; ?>

<main class="container" role="main">
  <div class="card-header">Monthly Report</div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Type</th>
          <th>Quantity</th>
          <th>Weight (kg)</th>
          <th>Average Weight</th>
          <th>Recycle Date</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach($rows as $r): ?>
        <tr data-id="<?= htmlspecialchars($r['Recycle_Id']) ?>">
          <td><?= htmlspecialchars($r['Type']) ?></td>
          <td><input type="number" class="quantity-input" value="1" readonly></td>
          <td><?= htmlspecialchars(number_format($r['weight'], 2)) ?></td>
          <td><?= htmlspecialchars(number_format($average, 2)) ?></td>
          <td><?= htmlspecialchars($r['Recycle_Date']) ?></td>
        </tr>
        <?php endforeach; ?>
      </tbody>
    </table>
  </div>

  <div class="footer">&copy; <?= date('Y') ?> GreenPoint | Average Weight: <?= number_format($average,2) ?> kg</div>
</main>

<!-- No AJAX update, since recycle table has no quantity/status -->
</body>
</html>
