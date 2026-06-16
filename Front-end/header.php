<?php
// Ensure session is available for nav state.
if (session_status() === PHP_SESSION_NONE) {
  session_start();
}

$cssPath = __DIR__ . '/../style/style.css';
$cssVersion = is_file($cssPath) ? (string) filemtime($cssPath) : (string) time();
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Green Point — Save money, Save Earth</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="Transform your recycling into rewards with AI-powered detection. Earn Green Points for every recyclable item.">
  <link rel="stylesheet" href="../style/style.css?v=<?= htmlspecialchars($cssVersion) ?>">
</head>
<body>

<header class="site-header">
  <div class="header-container">
    <a class="brand" href="./index.php">
      <span>Green Point</span>
    </a>

    <nav class="main-nav">
      <a href="./index.php">Home</a>
      <a href="./index.php#about">About</a>
      <a href="./index.php#contact">Contact</a>
      <a href="./items.php">Items</a>

      <?php if (empty($_SESSION['user_id'])): ?>
        <a href="./login.php" class="btn btn-primary">Login</a>
      <?php else: ?>
        <a href="./dashboard.php">Dashboard</a>
        <a href="./redeem_rewards.php">Redeem Rewards</a>
        <a href="./logout.php" class="btn btn-outline">Logout</a>
        <a href="./profile.php" class="profile-circle" title="Profile">
          <?= htmlspecialchars(strtoupper(substr($_SESSION['user'] ?? 'U', 0, 1))) ?>
        </a>
      <?php endif; ?>
    </nav>
  </div>
</header>
