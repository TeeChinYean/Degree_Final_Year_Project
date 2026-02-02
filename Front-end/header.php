<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
require_once 'config.php';
?>
<header class="site-header">
  <link rel="stylesheet" href="../style/style.css">
  <div class="wrap"
       style="background-image:url('../img/background.jpg');
              background-size:cover;
              display:flex;
              align-items:center;
              justify-content:space-between;
              padding:8px 0;">
    <a class="brand" href="./index.php">
      <img src="../img/logo.jpg" alt="Green Point logo" height="48">
    </a>
    <nav>
      <strong><a href="./index.php">Home</a></strong>
      <strong><a href="./about.php">About</a></strong>
      <strong><a href="./items.php">Recycle Items</a></strong>
      <strong><a href="./contact.php">Contact</a></strong>
      <?php if (!empty($user['User_name'])): ?>
        <a href="./dashboard.php">Dashboard</a>
        <a href="./logout.php">Logout</a>
        <a href="./profile.php" class="profile-circle"
           style="background:#fff;color:#0f5b63;border-radius:50%;
                  width:36px;height:36px;display:inline-flex;
                  align-items:center;justify-content:center;
                  font-weight:bold;text-decoration:none;">
          <?= htmlspecialchars(strtoupper(substr($_SESSION['user'], 0, 1))) ?>
        </a>
      <?php else: ?>
        <a href="./login.php" style="font-weight:bold;">Login</a>
      <?php endif; ?>
    </nav>
  </div>
</header>
