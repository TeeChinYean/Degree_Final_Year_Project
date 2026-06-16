<?php
session_start();
require './config.php'; // provides $pdo

// ---------- Basic guards ----------
if (!isset($_SESSION['user_id'])) {
    http_response_code(400);
    exit('Please login again.');
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
$user_id = (int)$_SESSION['user_id'];

// Primary source: session data. Fallback: hidden payload from form.
$data = $_SESSION['detectionResults'] ?? null;
if (!is_array($data) || empty($data)) {
    $rawPayload = $_POST['detection_payload'] ?? '';
    if (is_string($rawPayload) && $rawPayload !== '') {
        $decoded = json_decode($rawPayload, true);
        if (is_array($decoded) && !empty($decoded)) {
            $data = $decoded;
            // Keep a session copy for consistency in the current request lifecycle.
            $_SESSION['detectionResults'] = $decoded;
        }
    }
}

if (!is_array($data) || empty($data)) {
    http_response_code(400);
    exit('No data to insert');
}

// One-time confirmation guard (prevents double submit)
if (isset($_SESSION['confirmed_once'])) {
    http_response_code(409);
    exit('Already confirmed');
}
$_SESSION['confirmed_once'] = true;

function normalize_label(string $label): string {
    $label = strtolower(trim($label));
    $label = preg_replace('/[^a-z0-9]+/', '_', $label);
    return preg_replace('/_+/', '_', $label);
}

function parse_weight_grams($rawWeight): float {
    if (is_numeric($rawWeight)) {
        return (float)$rawWeight;
    }
    if (is_string($rawWeight) && preg_match('/-?\d+(\.\d+)?/', $rawWeight, $m)) {
        return (float)$m[0];
    }
    return 0.0;
}

function resolve_item_meta(PDO $pdo, string $itemName): ?array {
    static $resolvedCache = [];
    static $lookup = null;
    static $aliases = [
        'plastic' => 'plastic_bottle',
        'plastic_bottle' => 'plastic_bottle',
        'aluminium_can' => 'can',
        'aluminum_can' => 'can',
        'tin_can' => 'can',
        'can' => 'can',
        'glass_bottle' => 'glass_bottle',
        'paper' => 'paper',
        'steel_can' => 'steel_can',
        'wired' => 'wired',
    ];

    if ($lookup === null) {
        $lookup = [];
        $stmt = $pdo->query("SELECT item_id, type, points FROM item_types");
        foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $row) {
            $lookup[normalize_label((string)$row['type'])] = $row;
        }
    }

    $normalized = normalize_label($itemName);
    $candidateKeys = [$normalized];

    if (isset($aliases[$normalized])) {
        $candidateKeys[] = $aliases[$normalized];
    }
    if ($normalized === 'glass') {
        $candidateKeys[] = 'glass_bottle';
    }

    foreach ($candidateKeys as $key) {
        if (array_key_exists($key, $resolvedCache)) {
            return $resolvedCache[$key];
        }
        if (isset($lookup[$key])) {
            $resolvedCache[$key] = $lookup[$key];
            return $lookup[$key];
        }
    }

    foreach ($lookup as $typeKey => $row) {
        if (str_contains($typeKey, $normalized) || str_contains($normalized, $typeKey)) {
            $resolvedCache[$normalized] = $row;
            return $row;
        }
    }

    $resolvedCache[$normalized] = null;
    return null;
}

try {
    // ---------- Atomic transaction ----------
    $pdo->beginTransaction();

    // Prepare insert once
    $insertStmt = $pdo->prepare("
        INSERT INTO recycle (User_id, Item_type_id, weight, Recycle_Date)
        VALUES (?, ?, ?, NOW())
    ");

    $savedCount = 0;
    $calculatedTotalPoints = 0;
    $itemSummary = [];
    foreach ($data as $entry) {

        if (
            !is_array($entry) ||
            !isset($entry['item'], $entry['weight'])
        ) {
            continue;
        }

        $itemName = trim($entry['item']);
        $weight   = parse_weight_grams($entry['weight']);
        $meta     = resolve_item_meta($pdo, $itemName);

        if (
            !$meta ||
            $weight <= 0
        ) {
            continue;
        }

        $insertStmt->execute([
            $user_id,
            (int)$meta['item_id'],
            (float)$weight
        ]);
        $savedCount++;

        $pointsPer100g = (float)$meta['points'];
        $calculatedTotalPoints += (int) round(($weight / 100) * $pointsPer100g);

        $typeName = (string)$meta['type'];
        if (!isset($itemSummary[$typeName])) {
            $itemSummary[$typeName] = ['count' => 0, 'weight' => 0.0];
        }
        $itemSummary[$typeName]['count'] += 1;
        $itemSummary[$typeName]['weight'] += (float)$weight;
    }

    // Update user balance (atomic increment)
    $updateStmt = $pdo->prepare("
        UPDATE users
        SET balance = balance + :points
        WHERE user_id = :user_id
    ");

    $updateStmt->execute([
        ':points'  => $calculatedTotalPoints,
        ':user_id' => $user_id
    ]);

    $pdo->commit();

    // ---------- Cleanup ----------
    unset($_SESSION['detectionResults']);
    unset($_SESSION['confirmed_once']);
    $_SESSION['last_confirm_result'] = [
        'saved_count'   => $savedCount,
        'total_points'  => $calculatedTotalPoints,
        'confirmed_at'  => time(),
        'items'         => $itemSummary,
    ];
    header('Location: ./result_card.php');
    exit;

} catch (Throwable $e) {
    $pdo->rollBack();
    unset($_SESSION['confirmed_once']);
    http_response_code(500);
    exit('Transaction failed');
}
