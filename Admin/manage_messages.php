<?php
session_start();
require 'includes/db.php';

if (empty($_SESSION['Admin_id'])) {
  header('Location: login.php');
  exit;
}

require 'includes/header.php';

// Fetch messages with username
$stmt = $pdo->query("
  SELECT m.Contact_Id, m.User_id, u.User_name AS User_name, m.Message, m.created_at, m.status, u.User_email 
  FROM contact_messages m
  JOIN users u ON m.User_id = u.User_id
  ORDER BY m.created_at DESC
");
$messages = $stmt->fetchAll();
?>

<main class="admin-main">
  <h1 class="admin-title">Manage Messages</h1>
  <p class="admin-subtitle">Read user feedback and reply directly from the panel.</p>

  <?php if (isset($_GET['sent'])): ?>
    <div class="alert alert-success">✅ Reply sent successfully.</div>
  <?php elseif (isset($_GET['error']) && $_GET['error'] === 'mail'): ?>
    <div class="alert alert-error">❌ Reply saved but email failed to send.</div>
  <?php endif; ?>

  <?php foreach($messages as $msg): ?>
  <div class="msg-card">
    <div class="msg-head">
      <h3><?= htmlspecialchars($msg['User_name']) ?></h3>
      <div class="msg-meta">User ID: <?= (int)$msg['User_id'] ?></div>
      <div class="msg-meta">Received: <?= htmlspecialchars($msg['created_at']) ?></div>
    </div>

    <div class="msg-body"><?= nl2br(htmlspecialchars($msg['Message'])) ?></div>

    <?php if ($msg['status'] == 0): ?>
      <form method="post" action="reply_message.php" style="margin-top:12px;">
        <input type="hidden" name="message_id" value="<?= $msg['Contact_Id'] ?>">
        <input type="hidden" name="email" value="<?= htmlspecialchars($msg['User_email']) ?>">
        <textarea class="textarea" name="reply" placeholder="Write your reply..." required></textarea>
        <div style="margin-top:10px;display:flex;justify-content:flex-end;">
          <button class="btn btn-primary" type="submit">Send Reply</button>
        </div>
      </form>
    <?php else: ?>
      <div class="msg-replied"><span class="pill pill--ok">Replied</span></div>
    <?php endif; ?>
  </div>
  <?php endforeach; ?>
</main>

<?php require 'includes/footer.php'; ?>
