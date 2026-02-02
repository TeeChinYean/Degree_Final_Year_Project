<?php
session_start();
require './config.php';

// Redirect if not logged in
if (empty($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$user_id = (int)$_SESSION['user_id'];

// Handle profile updates
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Determine which form was submitted
    if (isset($_POST['update_profile'])) {
        $name = trim($_POST['name'] ?? '');
        $gmail = trim($_POST['gmail'] ?? '');

        if ($name !== '' && $gmail !== '') {
            $stmt = $pdo->prepare("UPDATE users SET User_name = ?, User_email = ? WHERE User_id = ?");
            $stmt->execute([$name, $gmail, $user_id]);
            $saved = true;
        }
    }

    // Handle password change
    if (isset($_POST['change_password'])) {
        $current = $_POST['current_password'] ?? '';
        $new = $_POST['new_password'] ?? '';
        $confirm = $_POST['confirm_password'] ?? '';

        // Fetch current password hash
        $stmt = $pdo->prepare("SELECT Password FROM users WHERE User_id = ?");
        $stmt->execute([$user_id]);
        $user_pw = $stmt->fetchColumn();

        if ($user_pw && password_verify($current, $user_pw)) {
            if ($new === $confirm && strlen($new) >= 6) {
                $hashed = password_hash($new, PASSWORD_DEFAULT);
                $stmt = $pdo->prepare("UPDATE users SET Password = ? WHERE User_id = ?");
                $stmt->execute([$hashed, $user_id]);
                $pw_success = true;
            } else {
                $pw_error = "New passwords do not match or are too short (min 6 characters).";
            }
        } else {
            $pw_error = "Current password is incorrect.";
        }
    }
}

// Fetch user info
$stmt = $pdo->prepare("SELECT * FROM users WHERE User_id = ?");
$stmt->execute([$user_id]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);

include './header.php';
?>

<main style="max-width:900px;margin:36px auto;padding:20px;text-align:center;font-family:Arial, sans-serif;">
  <!-- Profile Circle -->
  <div style="margin:0 auto;width:160px;height:160px;border-radius:50%;
              background:#0f5b63;color:#fff;display:flex;align-items:center;
              justify-content:center;font-weight:700;font-size:40px;">
    <?= htmlspecialchars(strtoupper(substr($user['User_name'], 0, 1))) ?>
  </div>

  <h2 style="margin-top:18px;color:#0f5b63;"><?= htmlspecialchars($user['User_name']) ?></h2>
  <p style="color:#555;"><?= htmlspecialchars($user['User_email']) ?></p>

  <div style="max-width:520px;margin:22px auto;text-align:left;">

    <!-- Profile Update Message -->
    <?php if (!empty($saved)): ?>
      <div style="color:green;padding:8px;border:1px solid #cceacc;margin-bottom:10px;text-align:center;">
        Profile updated successfully.
      </div>
    <?php endif; ?>

    <!-- Password Change Message -->
    <?php if (!empty($pw_success)): ?>
      <div style="color:green;padding:8px;border:1px solid #cceacc;margin-bottom:10px;text-align:center;">
        Password changed successfully.
      </div>
    <?php elseif (!empty($pw_error)): ?>
      <div style="color:red;padding:8px;border:1px solid #e6b5b5;margin-bottom:10px;text-align:center;">
        <?= htmlspecialchars($pw_error) ?>
      </div>
    <?php endif; ?>

    <!-- Edit Profile Form -->
    <form method="post">
      <label style="display:block;margin-bottom:8px;">Full Name
        <input name="name" value="<?= htmlspecialchars($user['User_name']) ?>"
               style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc;">
      </label>

      <label style="display:block;margin-bottom:8px;">Gmail
        <input name="gmail" type="email" value="<?= htmlspecialchars($user['User_email']) ?>"
               style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc;">
      </label>

      <div style="text-align:center;margin-top:12px;">
        <button name="update_profile" type="submit"
                style="background:#0f5b63;color:#fff;padding:10px 16px;
                       border-radius:6px;border:none;cursor:pointer;">
          Save Changes
        </button>
      </div>
    </form>

    <hr style="margin:28px 0;">

    <!-- Change Password Form -->
    <h3 style="color:#0f5b63;text-align:center;">Change Password</h3>
    <form method="post">
      <label style="display:block;margin-bottom:8px;">Current Password
        <input name="current_password" type="password" required
               style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc;">
      </label>

      <label style="display:block;margin-bottom:8px;">New Password
        <input name="new_password" type="password" required minlength="6"
               style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc;">
      </label>

      <label style="display:block;margin-bottom:8px;">Confirm New Password
        <input name="confirm_password" type="password" required minlength="6"
               style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc;">
      </label>

      <div style="text-align:center;margin-top:12px;">
        <button name="change_password" type="submit"
                style="background:#0f5b63;color:#fff;padding:10px 16px;
                       border-radius:6px;border:none;cursor:pointer;">
          Update Password
        </button>
      </div>
    </form>

    <div style="text-align:center;margin-top:20px;">
      <a href="logout.php" style="color:#0f5b63;text-decoration:none;">Logout</a>
    </div>
  </div>
</main>

<?php include './footer.php'; ?>
