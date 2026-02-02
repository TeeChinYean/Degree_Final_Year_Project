<?php
require './config.php';
session_start();

// Redirect if already logged in
if (!empty($_SESSION['user_id'])) {
    header('Location: ./dashboard.php');
    exit;
}

$err = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username']);
    $password = $_POST['password'];

    $stmt = $pdo->prepare('SELECT User_id, password FROM users WHERE User_name = ?');
    $stmt->execute([$username]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($user && password_verify($password, $user['password'])) {
        $_SESSION['user_id'] = $user['User_id'];
        $_SESSION['user'] = $user['User_name'];
        header('Location: ./dashboard.php');
        exit;
    } else {
        $err = 'Invalid username or password.';
    }
}

include './header.php';
?>
<div class="wrap" style="padding:24px 0;max-width:500px;margin:auto;text-align:center">
  <h1>User Login</h1>

  <?php if ($err): ?>
    <p style="color:red"><?= htmlspecialchars($err) ?></p>
  <?php endif; ?>

  <form method="post" style="margin-top:16px">
    <label>Username<br>
      <input name="username" required style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc">
    </label><br><br>

    <label>Password<br>
      <input name="password" type="password" required style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc">
    </label><br><br>

    <button class="btn" style="padding:10px 20px;background:#0f5b63;color:#fff;border:none;border-radius:6px;cursor:pointer">Login</button>
  </form>

  <hr style="margin:30px 0">

</div>
<?php include './footer.php'; ?>
