<?php
session_start();
require 'includes/db.php';
require 'includes/header.php';

if (empty($_SESSION['Admin_id'])) {
  header('Location: login.php');
  exit;
}

// Pagination setup
$limit = isset($_GET['show_all']) ? 0 : 10;
$page = max(1, (int)($_GET['page'] ?? 1));
$offset = ($page - 1) * $limit;

// Search logic
$search = trim($_GET['search'] ?? '');
$where = '';
$params = [];

if ($search !== '') {
  $where = "WHERE User_name LIKE ? OR User_email LIKE ?";
  $params = ["%$search%", "%$search%"];
}

// Count total users
$total_stmt = $pdo->prepare("SELECT COUNT(*) FROM users $where");
$total_stmt->execute($params);
$total = $total_stmt->fetchColumn();

// Fetch paginated users
$sql = "SELECT User_id, User_name, User_email, status, date FROM users $where ORDER BY date DESC";
if ($limit > 0) $sql .= " LIMIT $limit OFFSET $offset";
$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$rows = $stmt->fetchAll();
?>
<main style="max-width:1000px;margin:36px auto;padding:20px">
  <h2 style="background:#0f5b63;color:#fff;padding:12px;border-radius:6px">Manage Users</h2>

  <!-- Search bar -->
  <form method="get" style="margin:12px 0;display:flex;gap:8px">
    <input type="text" name="search" placeholder="Search by username or email..." 
           value="<?= htmlspecialchars($search) ?>"
           style="flex:1;padding:8px;border-radius:6px;border:1px solid #ccc">
    <button type="submit" style="background:#0f5b63;color:#fff;border:none;border-radius:6px;padding:8px 16px;cursor:pointer">Search</button>
    <a href="user_manage.php" style="background:#444;color:#fff;border:none;border-radius:6px;padding:8px 16px;text-decoration:none">Manage User</a>
  </form>

  <!-- Table -->
  <table style="width:100%;border-collapse:collapse;margin-top:16px">
    <thead style="background:#eef4ff">
      <tr>
        <th style="padding:10px;text-align:left;border-bottom:1px solid #ccc">Username</th>
        <th style="padding:10px;text-align:left;border-bottom:1px solid #ccc">Email</th>
        <th style="padding:10px;text-align:left;border-bottom:1px solid #ccc">Status</th>
        <th style="padding:10px;text-align:left;border-bottom:1px solid #ccc">Created</th>
      </tr>
    </thead>
    <tbody>
      <?php if (!$rows): ?>
        <tr><td colspan="4" style="padding:12px">No users found.</td></tr>
      <?php else: ?>
        <?php foreach ($rows as $r): ?>
          <tr>
            <td><?= htmlspecialchars($r['User_name']) ?></td>
            <td><?= htmlspecialchars($r['User_email']) ?></td>
            <td style="color:<?= $r['status']==0?'green':'red' ?>"><?= htmlspecialchars($r['status']) ?></td>
            <td><?= htmlspecialchars($r['date']) ?></td>
          </tr>
        <?php endforeach; ?>
      <?php endif; ?>
    </tbody>
  </table>

  <!-- Pagination controls -->
  <?php if ($limit > 0 && $total > $limit): ?>
    <div style="margin-top:14px;text-align:center">
      <?php if ($page > 1): ?>
        <a href="?page=<?= $page-1 ?>&search=<?= urlencode($search) ?>" style="margin-right:8px">← Prev</a>
      <?php endif; ?>
      <span>Page <?= $page ?> of <?= ceil($total/$limit) ?></span>
      <?php if ($offset + $limit < $total): ?>
        <a href="?page=<?= $page+1 ?>&search=<?= urlencode($search) ?>" style="margin-left:8px">Next →</a>
      <?php endif; ?>
      <a href="?show_all=1" style="margin-left:14px;color:#0f5b63">Show All</a>
    </div>
  <?php endif; ?>
</main>
<?php require 'includes/footer.php'; ?>
