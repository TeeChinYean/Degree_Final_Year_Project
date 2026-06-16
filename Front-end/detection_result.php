<?php
session_start();
require './config.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: ./login.php');
    exit;
}

if (!isset($_SESSION['detectionResults']) || empty($_SESSION['detectionResults'])) {
    header("Location: camera.php");
    exit();
}

unset($_SESSION['confirmed_once']);
$data = $_SESSION['detectionResults'];

function normalize_label(string $label): string {
    $label = strtolower(trim($label));
    $label = str_replace(['-', ' '], '_', $label);
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
    static $cache = [];
    static $aliases = [
        'plastic_bottle' => 'plastic-bottle',
        'plastic' => 'plastic-bottle',
        'aluminium_can' => 'can',
        'aluminum_can' => 'can',
        'can' => 'can',
        'glass_bottle' => 'glass bottle',
        'paper' => 'paper',
        'steel_can' => 'steel can',
        'wired' => 'wired',
    ];

    $normalized = normalize_label($itemName);
    $lookup = $aliases[$normalized] ?? str_replace('_', ' ', $normalized);

    if (array_key_exists($lookup, $cache)) {
        return $cache[$lookup];
    }

    $stmt = $pdo->prepare("
        SELECT item_id, type, points
        FROM item_types
        WHERE LOWER(type) = LOWER(?)
        LIMIT 1
    ");
    $stmt->execute([$lookup]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    $cache[$lookup] = $row ?: null;
    return $cache[$lookup];
}

$totalWeight = 0;
$totalPoints = 0;
$itemCounts = [];

foreach ($data as $entry) {
    $itemName = trim($entry['item']);
    $weight   = parse_weight_grams($entry['weight'] ?? 0);

    $totalWeight += $weight;

    $meta = resolve_item_meta($pdo, $itemName);
    if ($meta) {
        $pointsPer100g = (float)$meta['points'];
        $rawPoints = ($weight / 100) * $pointsPer100g;
        $totalPoints += (int) round($rawPoints);
    }
    
    if (!isset($itemCounts[$itemName])) {
        $itemCounts[$itemName] = ['count' => 0, 'weight' => 0];
    }
    $itemCounts[$itemName]['count']++;
    $itemCounts[$itemName]['weight'] += $weight;
}

include './header.php';
?>

<main class="wrap container">
    <div class="page-header">
        <h1>Verify Detection Results</h1>
        <p class="page-subtitle">Review your detected items before confirming</p>
    </div>

    <div class="detection-result-grid">
        <div class="detection-table-card">
            <div class="card-header">
                <h2>Detected Items</h2>
                <span class="item-count-badge"><?= count($data) ?> items</span>
            </div>
            
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Item Type</th>
                            <th>Weight (g)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($data as $entry): ?>
                            <tr>
                                <td>
                                    <strong><?= htmlspecialchars($entry['item']) ?></strong>
                                </td>
                                <td><?= number_format(parse_weight_grams($entry['weight'] ?? 0), 0); ?>g</td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="summary-card">
            <div class="summary-header">
                <h2>Transaction Summary</h2>
            </div>
            
            <div class="summary-content">
                <div class="summary-item">
                    <span class="summary-label">Total Items</span>
                    <span class="summary-value"><?= count($data) ?></span>
                </div>
                
                <div class="summary-item">
                    <span class="summary-label">Total Weight</span>
                    <span class="summary-value"><?= number_format($totalWeight, 0); ?>g</span>
                </div>
                
                <div class="summary-divider"></div>
                
                <div class="summary-item summary-total">
                    <span class="summary-label">Points Earned</span>
                    <span class="summary-value points-highlight">+<?= $totalPoints ?></span>
                </div>
            </div>
            
            <form action="confirm_result.php" method="post" class="summary-actions">
                <input type="hidden" name="total_weight" value="<?= $totalWeight ?>">
                <input type="hidden" name="total_points" value="<?= $totalPoints ?>">
                <input type="hidden" name="detection_payload" value="<?= htmlspecialchars(json_encode($data), ENT_QUOTES, 'UTF-8') ?>">
                
                <button type="submit" name="action" value="confirm" class="btn btn-primary btn-block btn-large">
                    ✓ Confirm & Save Points
                </button>
                
                <button type="submit" name="action" value="cancel" class="btn btn-outline btn-block">
                    Cancel & Discard
                </button>
            </form>
        </div>
    </div>
</main>

<?php include './footer.php'; ?>
