<?php
session_start();
require './config.php'; // provides $pdo

// ---------- Basic guards ----------
if (!isset($_SESSION['user_id'], $_SESSION['detectionResults'])) {
    http_response_code(400);
    exit('No data to process');
}

$action = $_POST['action'] ?? '';

if (!in_array($action, ['confirm', 'cancel'], true)) {
    http_response_code(400);
    exit('Invalid action');
}

// ---------- Cancel path ----------
if ($action === 'cancel') {
    unset($_SESSION['detectionResults']);
    header('Location: ./index.php');
    exit;
}

// ---------- Confirm path ----------
$totalPoints = isset($_POST['total_points']) ? (int)$_POST['total_points'] : 0;
$user_id = (int)$_SESSION['user_id'];
$data = $_SESSION['detectionResults'];

// One-time confirmation guard (prevents double submit)
if (isset($_SESSION['confirmed_once'])) {
    http_response_code(409);
    exit('Already confirmed');
}
$_SESSION['confirmed_once'] = true;

// Item mapping
$itemMap = [
    'plastic-bottle' => 1,
    'can'            => 2,
    'Glass Bottle'   => 3,
    'paper'          => 4,
    'Steel Can'      => 5,
    'Wired'          => 6
];

try {
    // ---------- Atomic transaction ----------
    $pdo->beginTransaction();

    // Prepare insert once
    $insertStmt = $pdo->prepare("
        INSERT INTO recycle (User_id, Item_type_id, weight, Recycle_Date)
        VALUES (?, ?, ?, NOW())
    ");

    foreach ($data as $entry) {

        if (
            !is_array($entry) ||
            !isset($entry['item'], $entry['weight'])
        ) {
            continue;
        }

        $itemName = trim($entry['item']);
        $weight   = $entry['weight'];

        if (
            !isset($itemMap[$itemName]) ||
            !is_numeric($weight) ||
            $weight <= 0
        ) {
            continue;
        }

        $insertStmt->execute([
            $user_id,
            $itemMap[$itemName],
            (float)$weight
        ]);
    }

    // Update user balance (atomic increment)
    $updateStmt = $pdo->prepare("
        UPDATE users
        SET balance = balance + :points
        WHERE user_id = :user_id
    ");

    $updateStmt->execute([
        ':points'  => $totalPoints,
        ':user_id' => $user_id
    ]);

    $pdo->commit();

    // ---------- Cleanup ----------
    unset($_SESSION['detectionResults']);
    unset($_SESSION['confirmed_once']);
    header('Location: ./index.php?status=success');
    exit;

} catch (Throwable $e) {
    $pdo->rollBack();
    unset($_SESSION['confirmed_once']);
    http_response_code(500);
    exit('Transaction failed');
}
