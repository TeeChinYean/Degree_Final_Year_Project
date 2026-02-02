<?php
require './config.php';
session_start();
if(!isset($_SESSION['user_id'])) header('Location: ./login.php');
$user_id = $_SESSION['user_id'];
$stmt = $pdo->prepare('SELECT User_name,balance FROM users WHERE User_id=?');
$stmt->execute([$user_id]);
$user = $stmt->fetch();
include './header.php';
?>
<div class="wrap" style="padding:24px 0">
  <h1>Dashboard</h1>
  <p>Welcome back, <?php echo htmlspecialchars($user['User_name']); ?>. Your balance: <strong><?php echo (int)$user['balance']; ?></strong> Green Points.</p>

  <section>
    <h2>Recent submissions</h2>
    <?php
      $s = $pdo->prepare('
          SELECT 
              r.recycle_id, 
              r.item_type_id, 
              i.type AS item_type, 
              r.count, 
              i.points, 
              r.recycle_date
          FROM recycle r
          JOIN item_types i ON r.item_type_id = i.item_id
          WHERE r.user_id = ?
          ORDER BY r.recycle_date DESC
          LIMIT 10
        ');
      $s->execute([$user_id]);


      $s->execute([$user_id]);
      $rows = $s->fetchAll();
      if (!$rows) {
        echo '<p style="padding:12px;color:#555;">No submissions yet.</p>';
      } else {
        echo '<table style="width:100%;border-collapse:collapse;margin-top:10px">';
        echo '<tr style="background:#f0f7f6"><th style="padding:8px;border-bottom:1px solid #ccc">Type</th>
              <th style="padding:8px;border-bottom:1px solid #ccc">Count</th>
              <th style="padding:8px;border-bottom:1px solid #ccc">Points</th>
              <th style="padding:8px;border-bottom:1px solid #ccc">Date</th></tr>';
        foreach ($rows as $r) {
          echo '<tr>
                  <td style="padding:8px;border-bottom:1px solid #eee">'.htmlspecialchars($r['type']).'</td>
                  <td style="padding:8px;border-bottom:1px solid #eee">'.(int)$r['count'].'</td>
                  <td style="padding:8px;border-bottom:1px solid #eee">'.(int)$r['points'].'</td>
                  <td style="padding:8px;border-bottom:1px solid #eee">'.htmlspecialchars(date('Y-m-d', strtotime($r['created_at']))).'</td>
                </tr>';
        }
        echo '</table>';
      }
          ?>
  </section>
</div>
<?php include './footer.php'; ?>