<?php
session_start();
require 'includes/db.php';
require 'includes/header.php';

if (empty($_SESSION['Admin_id'])) {
    header('Location: login.php');
    exit;
}

$message = '';
$message_type = ''; // success | error

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username'] ?? '');
    $action = $_POST['action'] ?? '';

    if ($username !== '' && in_array($action, ['ban', 'reactivate'])) {
        // Check if user exists first
        $check = $pdo->prepare("SELECT User_id, status FROM users WHERE User_name=?");
        $check->execute([$username]);
        $user = $check->fetch();

        if ($user) {
            $new_status = $action === 'ban' ? 1 : 0; // 1=inactive, 0=active
            $stmt = $pdo->prepare("UPDATE users SET status=? WHERE User_name=?");
            $stmt->execute([$new_status, $username]);

            $message = "User '<b>" . htmlspecialchars($username) . "</b>' has been successfully "
              . ($new_status ? "<span style='color:red'>deactivated</span>." 
                                    : "<span style='color:green'>reactivated</span>.");
            $message_type = 'success';
        } else {
            $message = "User '<b>" . htmlspecialchars($username) . "</b>' not found.";
            $message_type = 'error';
        }
    } else {
        $message = "Please enter a valid username and action.";
        $message_type = 'error';
    }
}
?>
<main style="max-width:700px;margin:36px auto;padding:20px;text-align:center">
  <h2 style="background:#0f5b63;color:#fff;padding:12px;border-radius:6px">Manage User Account</h2>

  <?php if ($message): ?>
    <div style="
      margin-top:16px;
      padding:12px;
      border-radius:8px;
      <?php if ($message_type === 'success'): ?>
        background:#e8ffe8; color:#155724; border:1px solid #c3e6cb;
      <?php else: ?>
        background:#ffe8e8; color:#721c24; border:1px solid #f5c6cb;
      <?php endif; ?>
    ">
      <?= $message ?>
    </div>
  <?php endif; ?>

  <form method="post" style="margin-top:20px">
    <label>Enter Username<br>
      <input type="text" name="username" required 
            style="width:80%;padding:8px;border:1px solid #ccc;border-radius:6px">
    </label><br><br>
    <button name="action" value="ban" 
            style="background:#d9534f;color:#fff;border:none;border-radius:6px;padding:10px 16px;cursor:pointer">Deactivate</button>
    <button name="action" value="reactivate" 
            style="background:#5cb85c;color:#fff;border:none;border-radius:6px;padding:10px 16px;cursor:pointer">Reactivate</button>
  </form>

  <div style="margin-top:20px">
    <a href="manage_users.php" style="color:#0f5b63;text-decoration:none">← Back to User List</a>
  </div>
</main>
<?php require 'includes/footer.php'; ?>
