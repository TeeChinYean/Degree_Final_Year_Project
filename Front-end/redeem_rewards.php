<?php
require './config.php';
session_start();

if (empty($_SESSION['user_id'])) {
    header('Location: ./login.php');
    exit;
}

$user_id = (int)$_SESSION['user_id'];

// Simple reward catalog (no DB migration needed)
$rewards = [
    ['id' => 'coupon_5',   'title' => '$5 Store Coupon',        'cost' => 50,  'desc' => 'Use in participating partners.'],
    ['id' => 'tote_bag',   'title' => 'Reusable Tote Bag',      'cost' => 120, 'desc' => 'A durable eco-friendly tote.'],
    ['id' => 'bottle',     'title' => 'Stainless Water Bottle', 'cost' => 200, 'desc' => 'Keeps drinks cold/hot longer.'],
    ['id' => 'tree_donate','title' => 'Plant a Tree (Donation)','cost' => 80,  'desc' => 'We donate to a tree-planting partner.'],
];

function findReward(array $rewards, string $id): ?array {
    foreach ($rewards as $r) {
        if (($r['id'] ?? '') === $id) return $r;
    }
    return null;
}

$flash = $_SESSION['flash_redeem'] ?? null;
unset($_SESSION['flash_redeem']);

// Handle redemption
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $rewardId = (string)($_POST['reward_id'] ?? '');
    $reward = findReward($rewards, $rewardId);

    if (!$reward) {
        $_SESSION['flash_redeem'] = ['type' => 'error', 'msg' => 'Invalid reward selected.'];
        header('Location: ./redeem_rewards.php');
        exit;
    }

    try {
        $pdo->beginTransaction();

        // Lock user row (prevents double spend)
        $stmt = $pdo->prepare('SELECT balance, User_name FROM users WHERE User_id = ? FOR UPDATE');
        $stmt->execute([$user_id]);
        $user = $stmt->fetch();

        if (!$user) {
            $pdo->rollBack();
            $_SESSION['flash_redeem'] = ['type' => 'error', 'msg' => 'User not found.'];
            header('Location: ./redeem_rewards.php');
            exit;
        }

        $balance = (int)($user['balance'] ?? 0);
        $cost = (int)$reward['cost'];

        if ($balance < $cost) {
            $pdo->rollBack();
            $_SESSION['flash_redeem'] = ['type' => 'error', 'msg' => 'Not enough Green Points for that reward.'];
            header('Location: ./redeem_rewards.php');
            exit;
        }

        $upd = $pdo->prepare('UPDATE users SET balance = balance - ? WHERE User_id = ?');
        $upd->execute([$cost, $user_id]);

        $pdo->commit();

        $_SESSION['flash_redeem'] = [
            'type' => 'success',
            'msg' => 'Redeemed: ' . $reward['title'] . ' (-' . $cost . ' points)'
        ];
        header('Location: ./redeem_rewards.php');
        exit;
    } catch (Throwable $e) {
        if ($pdo->inTransaction()) $pdo->rollBack();
        $_SESSION['flash_redeem'] = ['type' => 'error', 'msg' => 'Redemption failed. Please try again.'];
        header('Location: ./redeem_rewards.php');
        exit;
    }
}

// Load current user info
$stmt = $pdo->prepare('SELECT User_name, balance FROM users WHERE User_id = ?');
$stmt->execute([$user_id]);
$user = $stmt->fetch();

include './header.php';
?>

<main class="wrap container">
  <div class="page-header">
    <h1>Redeem Rewards</h1>
    <p class="page-subtitle">Spend your Green Points on eco-rewards.</p>
  </div>

  <div class="dashboard-stats" style="margin-bottom: 1.5rem;">
    <div class="stat-card stat-primary">
      <div class="stat-icon">⭐</div>
      <div class="stat-content">
        <div class="stat-value"><?= (int)($user['balance'] ?? 0) ?></div>
        <div class="stat-label">Green Points Available</div>
      </div>
    </div>
  </div>

  <?php if ($flash): ?>
    <div class="info-card" style="border-left: 6px solid <?= ($flash['type'] ?? '') === 'success' ? '#22c55e' : '#ef4444' ?>;">
      <p style="margin:0;"><strong><?= htmlspecialchars($flash['msg'] ?? '') ?></strong></p>
    </div>
  <?php endif; ?>

  <section class="info-card dashboard-section">
    <div class="section-header">
      <h2>Available Rewards</h2>
      <p class="section-subtitle">Choose a reward to redeem instantly.</p>
    </div>

    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;">
      <?php foreach ($rewards as $r): ?>
        <div class="info-card" style="margin:0;">
          <h3 style="margin:0 0 8px;"><?= htmlspecialchars($r['title']) ?></h3>
          <p style="margin:0 0 10px;opacity:.8;"><?= htmlspecialchars($r['desc']) ?></p>
          <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;">
            <span class="points-badge">Cost: <?= (int)$r['cost'] ?></span>
            <form method="post" action="./redeem_rewards.php" style="margin:0;">
              <input type="hidden" name="reward_id" value="<?= htmlspecialchars($r['id']) ?>">
              <button class="btn btn-primary" type="submit">Redeem</button>
            </form>
          </div>
        </div>
      <?php endforeach; ?>
    </div>
  </section>
</main>

<?php include './footer.php'; ?>

