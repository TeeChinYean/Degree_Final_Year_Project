<?php
session_start();
require 'includes/db.php';

// If already logged in, redirect to dashboard
if (!empty($_SESSION['Admin_id'])) {
    header('Location: index.php');
    exit;
}

$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['Admin_name'] ?? '');
    $password = trim($_POST['password'] ?? '');

    // Fetch Admin record by username
    $stmt = $pdo->prepare('SELECT Admin_id, Admin_password FROM Admin WHERE Admin_name = ?');
    $stmt->execute([$username]);
    $Admin = $stmt->fetch(PDO::FETCH_ASSOC);

    // Verify password
    if ($Admin && password_verify($password, $Admin['Admin_password'])) {
        $_SESSION['Admin_id'] = $Admin['Admin_id'];
        header('Location: index.php');
        exit;
    } else {
        $error = 'Invalid username or password.';
    }
}
?>
<?php
$cssPath = __DIR__ . '/../style/Admin.css';
$cssVersion = is_file($cssPath) ? (string) filemtime($cssPath) : (string) time();
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Admin Login — Green Point</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="stylesheet" href="../style/Admin.css?v=<?= htmlspecialchars($cssVersion) ?>">
</head>
<body>
  <main class="admin-auth">
    <div class="admin-auth-card">
      <h2>Admin Login</h2>
      <p>Sign in to manage users, types, reports, and messages.</p>

      <?php if ($error): ?>
        <div class="admin-error"><?= htmlspecialchars($error) ?></div>
      <?php endif; ?>

      <form method="post" autocomplete="off" style="display:grid;gap:12px;">
        <div>
          <label style="font-weight:800;color:#0b1220;">Admin Name</label>
          <input class="input" name="Admin_name" required>
        </div>

        <div>
          <label style="font-weight:800;color:#0b1220;">Password</label>
          <input class="input" name="password" type="password" required>
        </div>

        <div class="admin-auth-actions">
          <button class="btn btn-primary" type="submit">Login</button>
          <a class="btn btn-ghost" href="../Front-end/index.php">Back to site</a>
        </div>
      </form>
    </div>
  </main>
</body>
</html>
