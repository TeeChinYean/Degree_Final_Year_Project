<?php
require './config.php';
session_start(); // Always start session before using $_SESSION

// Handle form submission
$success = $error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (empty($_SESSION['user_id'])) {
        // User not logged in
        header('Location: ./login.php');
        exit;
    }

    $user_id = $_SESSION['user_id'];
    $message = trim($_POST['message'] ?? '');

    if ($message !== '') {
        $stmt = $pdo->prepare("INSERT INTO contact_messages (User_id, Message, created_at) VALUES (?, ?, NOW())");
        $stmt->execute([$user_id, $message]);
        $success = '✅ Your message has been sent successfully!';
    } else {
        $error = '⚠️ Message cannot be empty.';
    }
}
?>

<?php include './header.php'; ?>
<div class="wrap" style="padding:24px 0; max-width:700px; margin:auto;">
  <h1>Contact Us</h1>

  <?php if ($success): ?>
    <p style="color:green; background:#e8ffe8; padding:10px; border-radius:6px;"><?= htmlspecialchars($success) ?></p>
  <?php elseif ($error): ?>
    <p style="color:red; background:#ffe8e8; padding:10px; border-radius:6px;"><?= htmlspecialchars($error) ?></p>
  <?php endif; ?>

  <form method="post" style="margin-top:20px;">
    <label>Message<br>
      <textarea name="message" rows="6" required style="width:100%;padding:10px;border-radius:6px;border:1px solid #ccc;"></textarea>
    </label><br><br>
    <button class="btn" style="background:#0f5b63;color:#fff;padding:10px 20px;border:none;border-radius:6px;cursor:pointer;">Send</button>
  </form>
</div>
<div id="back-button" class="btn-container" style="margin-top:16px;">
        <button class="btn" onclick="Back()">Back</button>
    </div>
<?php include './footer.php'; ?>
<script>
  function Back() {
    window.history.back();
  }
</script>
