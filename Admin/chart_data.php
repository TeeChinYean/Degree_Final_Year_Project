<?php
// chart_data.php returns JSON aggregates used by chart.php
session_start();
header('Content-Type: application/json');

if (empty($_SESSION['Admin_id'])) {
    http_response_code(401);
    echo json_encode(['error' => 'login']);
    exit;
}

require 'includes/db.php';

// last 3 months (YYYY-MM)
$months = [];
for ($i = 2; $i >= 0; $i--) {
    $months[] = date('Y-m', strtotime("-{$i} months"));
}

// start date at beginning of first month in range
$start = $months[0] . '-01 00:00:00';

// Distinct item types from real tables
$stmt = $pdo->prepare("
    SELECT DISTINCT i.type AS type
    FROM recycle r
    JOIN item_types i ON r.item_type_id = i.item_id
    WHERE r.recycle_date >= ?
    ORDER BY i.type ASC
");
$stmt->execute([$start]);
$types = array_map(static fn($r) => (string)$r['type'], $stmt->fetchAll(PDO::FETCH_ASSOC));

// Totals per type (quantity = number of submissions)
$totals = [];
$stmt = $pdo->prepare("
    SELECT i.type AS type, COUNT(*) AS qty
    FROM recycle r
    JOIN item_types i ON r.item_type_id = i.item_id
    WHERE r.recycle_date >= ?
    GROUP BY i.type
");
$stmt->execute([$start]);
foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $r) {
    $totals[(string)$r['type']] = (int)$r['qty'];
}

// Monthly breakdown by type: $monthly['YYYY-MM']['Type'] = qty
$monthly = [];
$stmt = $pdo->prepare("
    SELECT DATE_FORMAT(r.recycle_date, '%Y-%m') AS ym, i.type AS type, COUNT(*) AS qty
    FROM recycle r
    JOIN item_types i ON r.item_type_id = i.item_id
    WHERE r.recycle_date >= ?
    GROUP BY ym, i.type
");
$stmt->execute([$start]);
foreach ($months as $m) {
    $monthly[$m] = [];
}
foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $r) {
    $ym = (string)$r['ym'];
    if (!isset($monthly[$ym])) {
        continue;
    }
    $monthly[$ym][(string)$r['type']] = (int)$r['qty'];
}

// Return JSON data for Chart.js
echo json_encode([
    'types' => $types,
    'months' => $months,
    'totals' => $totals,
    'monthly' => $monthly
]);
