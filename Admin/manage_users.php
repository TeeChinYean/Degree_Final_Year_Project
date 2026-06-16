<?php
session_start();
require 'includes/db.php';

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
<?php require 'includes/header.php'; ?>

<main class="admin-main">
  <h1 class="admin-title">Manage Users</h1>
  <p class="admin-subtitle">Search users, review status, and view created dates.</p>

  <!-- Search bar -->
  <div class="toolbar">
    <form method="get" class="toolbar-left">
      <input class="input" type="text" name="search" placeholder="Search by username or email..." value="<?= htmlspecialchars($search) ?>">
      <button class="btn btn-primary" type="submit">Search</button>
    </form>
    <div class="toolbar-right">
      <a class="btn btn-secondary" href="user_manage.php">Manage User</a>
    </div>
  </div>

  <!-- Table -->
  <div class="admin-card">
    <div class="admin-card-header">Users</div>
    <div class="admin-card-body" style="padding:0">
      <table class="table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <?php if (!$rows): ?>
            <tr><td colspan="4" class="text-center">No users found.</td></tr>
          <?php else: ?>
            <?php foreach ($rows as $r): ?>
              <tr>
                <td><strong><?= htmlspecialchars($r['User_name']) ?></strong></td>
                <td><?= htmlspecialchars($r['User_email']) ?></td>
                <td>
                  <?php if ((int)$r['status'] === 0): ?>
                    <span class="pill pill--ok">Active</span>
                  <?php else: ?>
                    <span class="pill pill--bad">Inactive</span>
                  <?php endif; ?>
                </td>
                <td><?= htmlspecialchars($r['date']) ?></td>
              </tr>
            <?php endforeach; ?>
          <?php endif; ?>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Pagination controls -->
  <?php if ($limit > 0 && $total > $limit): ?>
    <div style="margin-top:14px;text-align:center;color:rgba(255,255,255,.8);font-weight:700;">
      <?php if ($page > 1): ?>
        <a class="admin-link" href="?page=<?= $page-1 ?>&search=<?= urlencode($search) ?>" style="margin-right:8px;display:inline-flex;">← Prev</a>
      <?php endif; ?>
      <span>Page <?= $page ?> of <?= ceil($total/$limit) ?></span>
      <?php if ($offset + $limit < $total): ?>
        <a class="admin-link" href="?page=<?= $page+1 ?>&search=<?= urlencode($search) ?>" style="margin-left:8px;display:inline-flex;">Next →</a>
      <?php endif; ?>
      <a class="admin-link" href="?show_all=1" style="margin-left:14px;display:inline-flex;">Show All</a>
    </div>
  <?php endif; ?>
</main>
<?php require 'includes/footer.php'; ?>
