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
<main class="admin-main">
  <h1 class="admin-title">Admin Profile</h1>
  <p class="admin-subtitle">Update your details and password.</p>

  <div class="admin-card" style="margin-top:16px;">
    <div class="admin-card-header">Profile</div>
    <div class="admin-card-body">
      <div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;justify-content:center;">
        <div class="admin-avatar" style="width:88px;height:88px;font-size:28px;">
          <?= htmlspecialchars($Admin['Admin_name'] ? strtoupper(substr($Admin['Admin_name'],0,1)) : 'A') ?>
        </div>
        <div style="text-align:center;">
          <div style="font-weight:900;font-size:18px;"><?= htmlspecialchars($Admin['Admin_name']) ?></div>
          <div style="color:var(--muted);font-weight:700;"><?= htmlspecialchars($Admin['Admin_email']) ?></div>
        </div>
      </div>

      <?php if (!empty($saved)): ?>
        <div class="admin-success" style="margin-top:14px;">Profile updated successfully.</div>
      <?php endif; ?>

      <form method="post" style="margin-top:14px;display:grid;gap:12px;max-width:560px;margin-left:auto;margin-right:auto;">
        <div>
          <label style="font-weight:800;color:#0b1220;">Name</label>
          <input class="input" name="name" value="<?= htmlspecialchars($Admin['Admin_name']) ?>" required>
        </div>

        <div>
          <label style="font-weight:800;color:#0b1220;">Email</label>
          <input class="input" name="email" type="email" value="<?= htmlspecialchars($Admin['Admin_email']) ?>" required>
        </div>

        <div>
          <label style="font-weight:800;color:#0b1220;">New Password (optional)</label>
          <input class="input" name="new_password" type="password" placeholder="Leave blank to keep current">
        </div>

        <div style="display:flex;justify-content:flex-end;gap:10px;">
          <a class="btn btn-ghost" href="logout.php">Logout</a>
          <button class="btn btn-primary" type="submit">Save Changes</button>
        </div>
      </form>
    </div>
  </div>
</main>

<?php require 'includes/footer.php'; ?>
