<?php
session_start();
require 'includes/db.php';

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
<?php require 'includes/header.php'; ?>

<main class="admin-main">
  <h1 class="admin-title">Manage Item Types</h1>
  <p class="admin-subtitle">Add new recyclable types and control their active status.</p>

  <?php if ($message): ?>
    <div class="<?= $message_type==='success' ? 'admin-success' : 'admin-error' ?>" style="margin-top:14px;">
      <?= $message ?>
    </div>
  <?php endif; ?>

  <!-- Add new type form -->
  <div class="admin-card" style="margin-top:16px;">
    <div class="admin-card-header">Add New Type</div>
    <div class="admin-card-body">
      <form method="post">
        <div class="toolbar" style="margin:0;">
          <div class="toolbar-left" style="flex:1;">
            <input class="input" type="text" name="type" placeholder="Type name" required>
            <input class="input" type="text" name="examples" placeholder="Examples" required>
            <input class="input" type="number" name="points" placeholder="Points" min="1" required style="max-width:140px;">
          </div>
          <div class="toolbar-right">
            <button class="btn btn-primary" type="submit" name="add_type">Add Type</button>
          </div>
        </div>
      </form>
    </div>
  </div>

  <!-- Type list -->
  <div class="admin-card" style="margin-top:16px;">
    <div class="admin-card-header">Item Types</div>
    <div class="admin-card-body" style="padding:0;">
      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Examples</th>
            <th>Points</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <?php if (!$rows): ?>
            <tr><td colspan="6" class="text-center">No item types found.</td></tr>
          <?php else: ?>
            <?php foreach ($rows as $r): ?>
              <tr>
                <td><?= (int)$r['item_id'] ?></td>
                <td><strong><?= htmlspecialchars($r['type']) ?></strong></td>
                <td><?= htmlspecialchars($r['examples']) ?></td>
                <td><?= htmlspecialchars($r['points']) ?></td>
                <td>
                  <?php if ((int)$r['status'] === 0): ?>
                    <span class="pill pill--ok">Active</span>
                  <?php else: ?>
                    <span class="pill pill--bad">Inactive</span>
                  <?php endif; ?>
                </td>
                <td>
                  <form method="post" style="display:inline">
                    <input type="hidden" name="id" value="<?= (int)$r['item_id'] ?>">
                    <input type="hidden" name="status" value="<?= ((int)$r['status']===0) ? 1 : 0 ?>">
                    <button class="btn <?= ((int)$r['status']===0) ? 'btn-danger' : 'btn-primary' ?>" name="update_status" type="submit">
                      <?= ((int)$r['status']===0) ? 'Deactivate' : 'Reactivate' ?>
                    </button>
                  </form>
                </td>
              </tr>
            <?php endforeach; ?>
          <?php endif; ?>
        </tbody>
      </table>
    </div>
  </div>
</main>

<?php require 'includes/footer.php'; ?>
