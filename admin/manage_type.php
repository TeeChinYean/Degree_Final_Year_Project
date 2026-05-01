<?php
session_start();
require 'includes/db.php';
require 'includes/header.php';

if (empty($_SESSION['Admin_id'])) {
    header('Location: login.php');
    exit;
}

$message = '';
$message_type = '';

// Handle new type addition
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['add_type'])) {
    $type = trim($_POST['type'] ?? '');
    $examples = trim($_POST['examples'] ?? '');
    $points = (int)($_POST['points'] ?? 0);

    if ($type !== '' && $examples !== '' && $points > 0) {
        $stmt = $pdo->prepare("INSERT INTO item_types (type, examples, points, status) VALUES (?, ?, ?, 0)");
        $stmt->execute([$type, $examples, $points]);
        $message = "✅ New item type '<b>" . htmlspecialchars($type) . "</b>' added successfully.";
        $message_type = 'success';
    } else {
        $message = "⚠️ Please fill in all fields correctly.";
        $message_type = 'error';
    }
}

// Handle activate/deactivate actions
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['update_status'])) {
    $id = (int)$_POST['id'];
    $new_status = (int)$_POST['status']; // 0 or 1
    $stmt = $pdo->prepare("UPDATE item_types SET status=? WHERE item_id=?");
    $stmt->execute([$new_status, $id]);
    $message = "Item type status updated successfully.";
    $message_type = 'success';
}

// Fetch all item types
$stmt = $pdo->query("SELECT item_id, type, examples, points, status FROM item_types ORDER BY item_id ASC");
$rows = $stmt->fetchAll();
?>

<main style="max-width:1000px;margin:36px auto;padding:20px">
  <h2 style="background:#0f5b63;color:#fff;padding:12px;border-radius:6px">Manage Item Types</h2>

  <?php if ($message): ?>
    <div style="
      margin-top:16px;padding:12px;border-radius:8px;
      <?= $message_type==='success' ? 'background:#e8ffe8;color:#155724;border:1px solid #c3e6cb' : 'background:#ffe8e8;color:#721c24;border:1px solid #f5c6cb' ?>">
      <?= $message ?>
    </div>
  <?php endif; ?>

  <!-- Add new type form -->
  <form method="post" style="margin-top:20px;background:#f8f9fa;padding:16px;border-radius:8px">
    <h3>Add New Type</h3>
    <div style="display:flex;flex-wrap:wrap;gap:10px;">
      <input type="text" name="type" placeholder="Type name" required 
             style="flex:1;padding:8px;border-radius:6px;border:1px solid #ccc">
      <input type="text" name="examples" placeholder="Examples" required 
             style="flex:2;padding:8px;border-radius:6px;border:1px solid #ccc">
      <input type="number" name="points" placeholder="Points" min="1" required 
             style="width:100px;padding:8px;border-radius:6px;border:1px solid #ccc">
      <button type="submit" name="add_type" 
              style="background:#0f5b63;color:#fff;border:none;border-radius:6px;padding:8px 16px;cursor:pointer">
        Add
      </button>
    </div>
  </form>

  <!-- Type list -->
  <table style="width:100%;border-collapse:collapse;margin-top:20px">
    <thead style="background:#eef4ff">
      <tr>
        <th style="padding:10px;text-align:left;border-bottom:1px solid #ccc">ID</th>
        <th style="padding:10px;text-align:left;border-bottom:1px solid #ccc">Type</th>
        <th style="padding:10px;text-align:left;border-bottom:1px solid #ccc">Examples</th>
        <th style="padding:10px;text-align:left;border-bottom:1px solid #ccc">Points</th>
        <th style="padding:10px;text-align:left;border-bottom:1px solid #ccc">Status</th>
        <th style="padding:10px;text-align:left;border-bottom:1px solid #ccc">Action</th>
      </tr>
    </thead>
    <tbody>
      <?php if (!$rows): ?>
        <tr><td colspan="6" style="padding:12px">No item types found.</td></tr>
      <?php else: ?>
        <?php foreach ($rows as $r): ?>
          <tr>
            <td><?= $r['item_id'] ?></td>
            <td><?= htmlspecialchars($r['type']) ?></td>
            <td><?= htmlspecialchars($r['examples']) ?></td>
            <td><?= htmlspecialchars($r['points']) ?></td>
            <td style="color:<?= $r['status']==0 ? 'green':'red' ?>">
              <?= $r['status']==0 ? 'Active' : 'Inactive' ?>
            </td>
            <td>
              <form method="post" style="display:inline">
                <input type="hidden" name="id" value="<?= $r['item_id'] ?>">
                <input type="hidden" name="status" value="<?= $r['status']==0 ? 1 : 0 ?>">
                <button name="update_status" 
                        style="padding:6px 10px;border:none;border-radius:6px;color:#fff;
                        background:<?= $r['status']==0 ? '#d9534f' : '#5cb85c' ?>;cursor:pointer">
                  <?= $r['status']==0 ? 'Deactivate' : 'Reactivate' ?>
                </button>
              </form>
            </td>
          </tr>
        <?php endforeach; ?>
      <?php endif; ?>
    </tbody>
  </table>
</main>

<?php require 'includes/footer.php'; ?>
