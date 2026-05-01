<?php
session_start();
require 'includes/db.php';
require 'includes/header.php';

// Fetch messages with username
$stmt = $pdo->query("
  SELECT m.Contact_Id, m.User_id, u.User_name AS User_name, m.Message, m.Created_at, m.status, u.User_email 
  FROM contact_messages m
  JOIN users u ON m.User_id = u.User_id
  ORDER BY m.Created_at DESC
");
$messages = $stmt->fetchAll();
?>

<main style="max-width:1100px;margin:36px auto;padding:20px">
  <h2 style="background:#0f5b63;color:#fff;padding:12px;border-radius:6px;">Manage Messages</h2>

  <?php foreach($messages as $msg): ?>
  <div style="background:#fff;border:1px solid #ddd;border-radius:10px;padding:16px;box-shadow:0 2px 6px rgba(0,0,0,0.05);margin-bottom:16px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;">
      <h3 style="color:#0f5b63;margin:0;"><?= htmlspecialchars($msg['User_name']) ?></h3>
      <p style="margin:0;color:#555;">User ID: <?= $msg['User_id'] ?></p>
      <p style="margin:0;font-size:12px;color:#888;">Received: <?= $msg['Created_at'] ?></p>
    </div>

    <p style="margin:8px 0;font-size:14px;color:#333;"><?= nl2br(htmlspecialchars($msg['Message'])) ?></p>

    <?php if ($msg['status'] == 0): ?>
      <form method="post" action="reply_message.php" style="margin-top:10px;">
        <input type="hidden" name="message_id" value="<?= $msg['Contact_Id'] ?>">
        <input type="hidden" name="email" value="<?= htmlspecialchars($msg['User_email']) ?>">
        <textarea name="reply" placeholder="Write your reply..." required style="width:100%;padding:8px;border-radius:6px;border:1px solid #ccc;"></textarea>
        <button style="background:#0f5b63;color:#fff;padding:8px 16px;border:none;border-radius:6px;margin-top:6px;">Send Reply</button>
      </form>
    <?php else: ?>
      <p style="color:green;margin-top:8px;">✅ Replied</p>
    <?php endif; ?>
  </div>
  <?php endforeach; ?>
</main>

<?php require 'includes/footer.php'; ?>
