<?php
require './config.php';
session_start();

header('Content-Type: application/json');

if (empty($_SESSION['user_id'])) {
    http_response_code(401);
    echo json_encode(['error' => 'login']);
    exit;
}

$user_id = (int)$_SESSION['user_id'];

// last 6 months (YYYY-MM)
$months = [];
for ($i = 5; $i >= 0; $i--) {
    $months[] = date('Y-m', strtotime("-{$i} months"));
}
$start = $months[0] . '-01 00:00:00';

// types this user recycled in range
$stmt = $pdo->prepare("
    SELECT DISTINCT i.type AS type
    FROM recycle r
    JOIN item_types i ON r.item_type_id = i.item_id
    WHERE r.recycle_date >= ? AND r.user_id = ?
    ORDER BY i.type ASC
");
$stmt->execute([$start, $user_id]);
$types = array_map(static fn($r) => (string)$r['type'], $stmt->fetchAll(PDO::FETCH_ASSOC));

// totals by type (count + weight)
$totalsCount = [];
$totalsWeight = [];
$stmt = $pdo->prepare("
    SELECT i.type AS type, COUNT(*) AS qty, COALESCE(SUM(r.weight), 0) AS weight
    FROM recycle r
    JOIN item_types i ON r.item_type_id = i.item_id
    WHERE r.recycle_date >= ? AND r.user_id = ?
    GROUP BY i.type
");
$stmt->execute([$start, $user_id]);
foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $r) {
    $t = (string)$r['type'];
    $totalsCount[$t] = (int)$r['qty'];
    $totalsWeight[$t] = (float)$r['weight'];
}

// monthly totals weight: monthlyWeight['YYYY-MM'] = grams
$monthlyWeight = [];
foreach ($months as $m) {
    $monthlyWeight[$m] = 0.0;
}
$stmt = $pdo->prepare("
    SELECT DATE_FORMAT(r.recycle_date, '%Y-%m') AS ym, COALESCE(SUM(r.weight), 0) AS weight
    FROM recycle r
    WHERE r.recycle_date >= ? AND r.user_id = ?
    GROUP BY ym
");
$stmt->execute([$start, $user_id]);
foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $r) {
    $ym = (string)$r['ym'];
    if (!isset($monthlyWeight[$ym])) {
        continue;
    }
    $monthlyWeight[$ym] = (float)$r['weight'];
}

echo json_encode([
    'months' => $months,
    'types' => $types,
    'totalsCount' => $totalsCount,
    'totalsWeight' => $totalsWeight,
    'monthlyWeight' => $monthlyWeight
]);

