<?php
/**
 * run_migration.php — One-time DB migration runner
 * Access: http://localhost/Front-end/run_migration.php
 * DELETE this file after running!
 */
require './config.php';

$results = [];

$sqls = [
    'Create stations table' => "
        CREATE TABLE IF NOT EXISTS `stations` (
          `site_id`      VARCHAR(64)  NOT NULL,
          `station_name` VARCHAR(100) NOT NULL DEFAULT '',
          `station_ip`   VARCHAR(45)  NOT NULL DEFAULT '',
          `rtsp_port`    SMALLINT UNSIGNED NOT NULL DEFAULT 8554,
          `status`       ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
          `applied_at`   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `approved_at`  DATETIME NULL,
          `last_seen`    DATETIME NULL,
          `is_online`    TINYINT(1) NOT NULL DEFAULT 0,
          PRIMARY KEY (`site_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ",
    'Create user_station table' => "
        CREATE TABLE IF NOT EXISTS `user_station` (
          `user_id`    INT         NOT NULL,
          `station_id` VARCHAR(64) NOT NULL,
          `connected_at` DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`user_id`),
          CONSTRAINT `fk_us_user`
            FOREIGN KEY (`user_id`) REFERENCES `users`(`User_id`)
            ON DELETE CASCADE ON UPDATE CASCADE,
          CONSTRAINT `fk_us_station`
            FOREIGN KEY (`station_id`) REFERENCES `stations`(`site_id`)
            ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    ",
    'Add connected_at column to existing user_station' => "
        ALTER TABLE `user_station` ADD COLUMN `connected_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ",
];

foreach ($sqls as $label => $sql) {
    try {
        $pdo->exec($sql);
        $results[] = ['ok' => true,  'label' => $label, 'msg' => 'Success'];
    } catch (Exception $e) {
        $results[] = ['ok' => false, 'label' => $label, 'msg' => $e->getMessage()];
    }
}


// Show existing tables
$tables = $pdo->query("SHOW TABLES")->fetchAll(PDO::FETCH_COLUMN);
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DB Migration</title>
<style>
  body { font-family: monospace; background: #0d1117; color: #e6edf3; padding: 2rem; }
  h1   { color: #58a6ff; }
  .ok  { color: #3fb950; }
  .err { color: #f85149; }
  .box { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem 1.5rem; margin: 1rem 0; }
  .warn { background: #2d1a00; border-color: #d29922; border-radius: 8px; padding: 1rem 1.5rem; margin: 1rem 0; color: #e3b341; }
</style>
</head>
<body>
<h1>🗄️ GreenPoint DB Migration</h1>

<?php foreach ($results as $r): ?>
<div class="box">
  <span class="<?= $r['ok'] ? 'ok' : 'err' ?>"><?= $r['ok'] ? '✅' : '❌' ?></span>
  <strong><?= htmlspecialchars($r['label']) ?></strong><br>
  <small><?= htmlspecialchars($r['msg']) ?></small>
</div>
<?php endforeach; ?>

<div class="box">
  <strong>📋 Tables in database:</strong><br><br>
  <?php foreach ($tables as $t): ?>
    &nbsp;&nbsp;<span class="ok">✓</span> <?= htmlspecialchars($t) ?><br>
  <?php endforeach; ?>
</div>

<div class="warn">
  ⚠️ <strong>Security:</strong> Delete this file after migration!<br>
  <code>F:\laragon\www\Front-end\run_migration.php</code>
</div>
</body>
</html>
