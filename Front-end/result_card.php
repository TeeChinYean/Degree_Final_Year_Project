<?php
session_start();
require './config.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: ./login.php');
    exit;
}

$result = $_SESSION['last_confirm_result'] ?? null;
if (!is_array($result)) {
    header('Location: ./index.php');
    exit;
}

$savedCount = (int)($result['saved_count'] ?? 0);
$totalPoints = (int)($result['total_points'] ?? 0);
$confirmedAt = (int)($result['confirmed_at'] ?? time());
$items = $result['items'] ?? [];

unset($_SESSION['last_confirm_result']);

include './header.php';
?>

<main class="wrap container">
    <div class="page-header">
        <h1>Submission Complete</h1>
        <p class="page-subtitle">Your recycle result has been saved successfully.</p>
    </div>

    <section class="summary-card" style="max-width:560px;margin:0 auto;">
        <div class="summary-header">
            <h2>Result Card</h2>
        </div>

        <div class="summary-content">
            <div class="summary-item">
                <span class="summary-label">Saved Entries</span>
                <span class="summary-value"><?= $savedCount ?></span>
            </div>

            <div class="summary-item">
                <span class="summary-label">Points Added</span>
                <span class="summary-value points-highlight">+<?= $totalPoints ?></span>
            </div>

            <div class="summary-item">
                <span class="summary-label">Confirmed Time</span>
                <span class="summary-value"><?= date('Y-m-d H:i:s', $confirmedAt) ?></span>
            </div>

            <?php if (!empty($items)): ?>
                <div class="summary-divider"></div>
                <?php foreach ($items as $type => $meta): ?>
                    <div class="summary-item">
                        <span class="summary-label"><?= htmlspecialchars((string)$type) ?> x <?= (int)($meta['count'] ?? 0) ?></span>
                        <span class="summary-value"><?= number_format((float)($meta['weight'] ?? 0), 1) ?>g</span>
                    </div>
                <?php endforeach; ?>
            <?php endif; ?>
        </div>

        <div class="summary-actions">
            <a href="./dashboard.php" class="btn btn-primary btn-block btn-large">确定，返回主页</a>
        </div>
    </section>
</main>

<?php include './footer.php'; ?>
