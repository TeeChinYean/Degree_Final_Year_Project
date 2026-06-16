<?php
if (session_status() === PHP_SESSION_NONE) {
  session_start();
}

$cssPath = __DIR__ . '/../../style/Admin.css';
$cssVersion = is_file($cssPath) ? (string) filemtime($cssPath) : (string) time();
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Green Point Admin</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="stylesheet" href="../style/Admin.css?v=<?= htmlspecialchars($cssVersion) ?>">
</head>
<body>

<header class="admin-header">
  <div class="admin-header-inner">
    <a class="admin-brand" href="index.php" aria-label="Green Point Admin Home">
      <span class="admin-brand-badge">GP</span>
      <span>Green Point Admin</span>
    </a>

    <nav class="admin-nav" aria-label="Admin navigation">
      <a class="admin-link" href="chart.php">Charts</a>
      <a class="admin-link" href="generate_pdf.php">Report PDF</a>
      <a class="admin-link" href="history.php">History</a>
      <a class="admin-link" href="manage_users.php">Users</a>
      <a class="admin-link" href="manage_type.php">Types</a>
      <a class="admin-link" href="manage_messages.php">Messages</a>
      <a class="admin-link" href="manage_stations.php">Stations</a>
      <a class="admin-link" href="live_view.php">Live View</a>
      <a class="admin-link admin-link--danger" href="logout.php">Logout</a>
      <a class="admin-avatar" href="profile.php" title="Profile">
        <?= htmlspecialchars(strtoupper(substr($_SESSION['Admin_name'] ?? 'A', 0, 1))) ?>
      </a>
    </nav>
  </div>
</header>
