<?php
require './config.php';
session_start();

$error = ""; 

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'];
    $user_name = $_POST['User_name'];
    // Check for duplicate
    $checkStmt = $pdo->prepare('SELECT User_id FROM users WHERE User_email = ?');
    $checkStmt->execute([$email]);
    
    if ($checkStmt->fetch()) {
        $error = "This email is already registered.";
    } else {
        $password = password_hash($_POST['password'], PASSWORD_DEFAULT);

        $insertStmt = $pdo->prepare(
            'INSERT INTO users 
            (User_name, Password, User_email, status, balance, date)
            VALUES (?, ?, ?, 0, 0, NOW())'
        );

        $insertStmt->execute([
            $user_name,
            $password,
            $email
        ]);
        header('Location: ./dashboard.php');
        exit;
    }
}
include './header.php'; ?>

<?php if ($error): ?>
<html>
<head>
  <meta charset="UTF-8">
  <title>Registration</title>
  <link rel="stylesheet" href="../style/style.css">
</head>
<div id="customModal" class="modal-overlay">
    <div class="modal-box">
        <h3>Notification</h3>
        <p><?php echo htmlspecialchars($error); ?></p>
        <button onclick="refreshPage()" class="btn">OK</button>
    </div>
</div>
<?php endif; ?>

<div class="wrap" style="padding:24px 0">
  <h1>Register</h1>
  <form method="post">
    <label>Username<br><input name="User_name" required></label><br><br>
    <label>Email<br><input name="email" type="email" required></label><br><br>
    <label>Password<br><input name="password" type="password" required></label><br><br>
    <button class="btn">Create account</button>
  </form>
</div>
<script>
function refreshPage() {
    // This clears the POST data and refreshes the page
    window.location.href = window.location.pathname;
}
</script>

<?php include './footer.php'; ?>
</html>
