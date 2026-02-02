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
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Admin Login</title>
  <style>
    body { font-family: Arial, sans-serif; width: 360px; margin: 80px auto; background: #f8f9fa; color: #333; }
    h2 { text-align: center; color: #0f5b63; }
    form { background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 0 8px rgba(0,0,0,0.1); }
    label { display: block; margin-bottom: 10px; font-weight: bold; }
    input { width: 100%; padding: 8px; border-radius: 5px; border: 1px solid #ccc; margin-top: 4px; }
    button { width: 100%; padding: 10px; background: #0f5b63; border: none; color: #fff; border-radius: 5px; margin-top: 10px; cursor: pointer; font-weight: bold; }
    button:hover { background: #0c474f; }
    .error { color: red; margin-bottom: 10px; text-align: center; }
  </style>
</head>
<body>
  <h2>Admin Login</h2>

  <?php if ($error): ?>
    <div class="error"><?= htmlspecialchars($error) ?></div>
  <?php endif; ?>

  <form method="post" autocomplete="off">
    <label>Admin Name
      <input name="Admin_name" required>
    </label>
    <label>Password
      <input name="password" type="password" required>
    </label>
    <button type="submit">Login</button>
  </form>
</body>
</html>
