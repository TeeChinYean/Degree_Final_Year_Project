<?php
session_start();
if (empty($_SESSION['Admin_id'])) {
    header('Location: login.php');
    exit;
}

require 'includes/db.php';

$Admin_id = (int)$_SESSION['Admin_id'];

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = trim($_POST['name'] ?? '');
    $email = trim($_POST['email'] ?? '');
    $newPassword = trim($_POST['new_password'] ?? '');

    // Update basic info
    $stmt = $pdo->prepare('UPDATE Admin SET Admin_name=?, Admin_email=? WHERE Admin_id=?');
    $stmt->execute([$name, $email, $Admin_id]);

    // Optional password update
    if ($newPassword !== '') {
        $hashed = password_hash($newPassword, PASSWORD_DEFAULT);
        $stmt = $pdo->prepare('UPDATE Admin SET Admin_password=? WHERE Admin_id=?');
        $stmt->execute([$hashed, $Admin_id]);
    }

    $saved = true;
}

// Fetch Admin data
$stmt = $pdo->prepare('SELECT * FROM Admin WHERE Admin_id=?');
$stmt->execute([$Admin_id]);
$Admin = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$Admin) {
    die('Admin record not found.');
}

require 'includes/header.php';
?>
<main style="max-width:900px;margin:36px auto;padding:20px;text-align:center">
  <div style="margin:0 auto;width:160px;height:160px;border-radius:50%;background:#0f5b63;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:20px">
    <?= htmlspecialchars($Admin['Admin_name'] ? strtoupper(substr($Admin['Admin_name'],0,1)) : 'A') ?>
  </div>

  <h2 style="margin-top:18px"><?= htmlspecialchars($Admin['Admin_name']) ?></h2>
  <p><?= htmlspecialchars($Admin['Admin_email']) ?></p>

  <div style="max-width:520px;margin:22px auto;text-align:left">
    <?php if (!empty($saved)): ?>
      <div style="color:green;padding:8px;border:1px solid #cceacc;margin-bottom:10px;border-radius:6px;background:#f4fff4">
        Profile updated successfully
      </div>
    <?php endif; ?>

    <form method="post">
      <label style="display:block;margin-bottom:8px">Name
        <input name="name" value="<?= htmlspecialchars($Admin['Admin_name']) ?>" required style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc">
      </label>

      <label style="display:block;margin-bottom:8px">Email
        <input name="email" type="email" value="<?= htmlspecialchars($Admin['Admin_email']) ?>" required style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc">
      </label>

      <label style="display:block;margin-bottom:8px">New Password (optional)
        <input name="new_password" type="password" placeholder="Leave blank to keep current" style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc">
      </label>

      <div style="text-align:center;margin-top:12px">
        <button style="background:#0f5b63;color:#fff;padding:10px 16px;border-radius:6px;border:none;cursor:pointer">
          Save Changes
        </button>
      </div>
    </form>

    <div style="text-align:center;margin-top:16px">
      <a href="logout.php" style="color:#0f5b63;text-decoration:none;font-weight:bold">Logout</a>
    </div>
  </div>
</main>

<?php require 'includes/footer.php'; ?>
