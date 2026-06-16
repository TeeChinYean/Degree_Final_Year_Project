<?php
session_start();
require './config.php';

// Redirect if not logged in
if (empty($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$user_id = (int)$_SESSION['user_id'];
$saved = false;
$pw_success = false;
$pw_error = '';

// Handle profile updates
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['update_profile'])) {
        $name = trim($_POST['name'] ?? '');
        $gmail = trim($_POST['gmail'] ?? '');

        if ($name !== '' && $gmail !== '') {
            $stmt = $pdo->prepare("UPDATE users SET User_name = ?, User_email = ? WHERE User_id = ?");
            $stmt->execute([$name, $gmail, $user_id]);
            $_SESSION['user'] = $name;
            $saved = true;
        }
    }

    if (isset($_POST['change_password'])) {
        $current = $_POST['current_password'] ?? '';
        $new = $_POST['new_password'] ?? '';
        $confirm = $_POST['confirm_password'] ?? '';

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

<main class="wrap container">
    <div class="profile-header">
        <div class="profile-avatar">
            <?= htmlspecialchars(strtoupper(substr($user['User_name'], 0, 1))) ?>
        </div>
        <div class="profile-info">
            <h1><?= htmlspecialchars($user['User_name']) ?></h1>
            <p class="profile-email"><?= htmlspecialchars($user['User_email']) ?></p>
            <?php if (isset($user['balance'])): ?>
                <p class="profile-balance">
                    <strong><?= (int)$user['balance']; ?></strong> Green Points
                </p>
            <?php endif; ?>
        </div>
    </div>

    <div class="profile-content">
        <section class="profile-section">
            <h2>Edit Profile</h2>
            
            <?php if ($saved): ?>
                <div class="alert success">
                    Profile updated successfully!
                </div>
            <?php endif; ?>

            <form method="post" class="profile-form">
                <div class="form-group">
                    <label for="name">Full Name</label>
                    <input 
                        id="name" 
                        name="name" 
                        type="text" 
                        value="<?= htmlspecialchars($user['User_name']) ?>"
                        required
                    >
                </div>

                <div class="form-group">
                    <label for="gmail">Email Address</label>
                    <input 
                        id="gmail" 
                        name="gmail" 
                        type="email" 
                        value="<?= htmlspecialchars($user['User_email']) ?>"
                        required
                    >
                </div>

                <button name="update_profile" type="submit" class="btn btn-primary">
                    Save Changes
                </button>
            </form>
        </section>

        <section class="profile-section">
            <h2>Change Password</h2>
            
            <?php if ($pw_success): ?>
                <div class="alert success">
                    Password changed successfully!
                </div>
            <?php elseif ($pw_error): ?>
                <div class="alert error">
                    <?= htmlspecialchars($pw_error) ?>
                </div>
            <?php endif; ?>

            <form method="post" class="profile-form">
                <div class="form-group">
                    <label for="current_password">Current Password</label>
                    <input 
                        id="current_password" 
                        name="current_password" 
                        type="password" 
                        required
                        placeholder="Enter your current password"
                    >
                </div>

                <div class="form-group">
                    <label for="new_password">New Password</label>
                    <input 
                        id="new_password" 
                        name="new_password" 
                        type="password" 
                        required 
                        minlength="6"
                        placeholder="At least 6 characters"
                    >
                    <small class="form-hint">Minimum 6 characters</small>
                </div>

                <div class="form-group">
                    <label for="confirm_password">Confirm New Password</label>
                    <input 
                        id="confirm_password" 
                        name="confirm_password" 
                        type="password" 
                        required 
                        minlength="6"
                        placeholder="Re-enter your new password"
                    >
                </div>

                <button name="change_password" type="submit" class="btn btn-primary">
                    Update Password
                </button>
            </form>
        </section>

        <div class="profile-actions">
            <a href="./dashboard.php" class="btn btn-outline">← Back to Dashboard</a>
        </div>
    </div>
</main>

<?php include './footer.php'; ?>
