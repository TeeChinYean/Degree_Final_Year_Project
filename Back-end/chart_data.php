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

// last 3 months
$months = [];
for ($i = 2; $i >= 0; $i--) {
    $months[] = date('Y-m', strtotime("-{$i} months"));
}

// get distinct item types in last 3 months
$start = date('Y-m-01', strtotime('-2 months'));
$stmt = $pdo->prepare("SELECT DISTINCT type FROM monthly_report WHERE submit_date >= ?");
$stmt->execute([$start]);
$types = array_map(fn($r) => $r['type'], $stmt->fetchAll(PDO::FETCH_ASSOC));

// total quantity per type (overall)
$totals = [];
if ($types) {
    $stmt = $pdo->prepare("SELECT type, SUM(quantity) AS qty FROM monthly_report WHERE submit_date >= ? GROUP BY type");
    $stmt->execute([$start]);
    foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $r) {
        $totals[$r['type']] = (int)$r['qty'];
    }
}

// monthly breakdown: e.g., $monthly['2025-08']['Plastic'] = 12
$monthly = [];
foreach ($months as $m) {
    $ym_start = $m . '-01';
    $ym_end = date('Y-m-t', strtotime($ym_start));

    $stmt = $pdo->prepare("
        SELECT type, SUM(quantity) AS qty
        FROM monthly_report
        WHERE submit_date BETWEEN ? AND ?
        GROUP BY type
    ");
    $stmt->execute([$ym_start, $ym_end]);

    $monthly[$m] = [];
    foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $r) {
        $monthly[$m][$r['type']] = (int)$r['qty'];
    }
}

// Return JSON data for Chart.js
echo json_encode([
    'types' => $types,
    'months' => $months,
    'totals' => $totals,
    'monthly' => $monthly
]);
