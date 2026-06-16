<?php
require 'includes/db.php';
session_start();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Sanitize input
    $username = trim($_POST['username']);
    $gmail = trim($_POST['gmail']);
    $password = password_hash($_POST['password'], PASSWORD_DEFAULT);

    try {
        // Insert into Admin table
        $stmt = $pdo->prepare('INSERT INTO Admin (Admin_name, Admin_email, Admin_password, Admin_image) VALUES (?, ?, ?, "")');
        $stmt->execute([$username, $gmail, $password]);

        // Save new Admin session
        $_SESSION['Admin_id'] = $pdo->lastInsertId();

        // Redirect to dashboard
        header('Location: index.php');
        exit;

    } catch (PDOException $e) {
        die('Error creating account: ' . htmlspecialchars($e->getMessage()));
    }
}

include 'includes/header.php';
?>

<div class="wrap" style="padding:24px 0; max-width:600px; margin:auto;">
  <h1>Admin Registration</h1>
  <form method="post" style="margin-top:20px;">
    <label>Username<br>
      <input name="username" required style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc">
    </label><br><br>

    <label>Password<br>
      <input name="password" type="password" required style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc">
    </label><br><br>

    <label>Gmail<br>
      <input name="gmail" type="email" required style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc">
    </label><br><br>

    <button class="btn" style="background:#0f5b63;color:#fff;padding:10px 16px;border-radius:6px;border:none">Create Account</button>
  </form>
</div>

<?php include 'includes/footer.php'; ?>
