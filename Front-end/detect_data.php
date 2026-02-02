<?php
session_start();

$flashes = $_SESSION['flashes'] ?? [];

foreach ($flashes as $flash): ?>
    <div style="border:1px solid green; padding:8px; margin:6px 0;">
        <strong>Status:</strong> <?= htmlspecialchars($flash['status']) ?><br>
        <strong>Item:</strong> <?= htmlspecialchars($flash['item']) ?><br>
        <strong>Weight:</strong> <?= number_format($flash['weight'], 2) ?> g<br>
        <small><?= date('H:i:s', $flash['time']) ?></small>
    </div>
<?php endforeach;
