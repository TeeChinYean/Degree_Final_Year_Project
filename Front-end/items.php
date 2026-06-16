<?php
require './config.php';
session_start();
include './header.php';

$stmt = $pdo->query('SELECT * FROM item_types ORDER BY Points DESC');
$items = $stmt->fetchAll();
?>

<main class="wrap container">
    <div class="page-header">
        <h1>Recyclable Item Types</h1>
        <p class="page-subtitle">Learn about different materials and their point values</p>
    </div>

    <div class="table-container">
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Icon</th>
                        <th>Material Type</th>
                        <th>Example Items</th>
                        <th>Points per 100g</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($items)): ?>
                        <tr>
                            <td colspan="4" class="empty-state">
                                <div class="empty-icon">📦</div>
                                <p><strong>No item types available at the moment.</strong></p>
                            </td>
                        </tr>
                    <?php else: ?>
                        <?php foreach($items as $it): ?>
                            <tr>
                                <td class="icon-cell">
                                    <?php if(!empty($it['Image'])): ?>
                                        <img src="../img/<?= htmlspecialchars($it['Image']) ?>" 
                                             alt="<?= htmlspecialchars($it['Type']) ?>" 
                                             class="item-icon">
                                    <?php else: ?>
                                        <span class="item-icon-placeholder">📦</span>
                                    <?php endif; ?>
                                </td>
                                <td>
                                    <strong class="item-type"><?= htmlspecialchars($it['Type']) ?></strong>
                                </td>
                                <td class="item-examples">
                                    <?= htmlspecialchars($it['Examples']) ?>
                                </td>
                                <td>
                                    <span class="badge badge-primary">
                                        <?= (int)$it['Points'] ?> pts
                                    </span>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>

        <div class="table-actions">
            <?php if(isset($_SESSION['user_id'])): ?>
                <form action="start_detect_setup.php" method="POST" style="display: inline;">
                    <button type="submit" id="start_detect" class="btn btn-primary btn-large">
                        🎯 Start Detecting Items
                    </button>
                </form>
            <?php else: ?>
                <a href="./login.php" class="btn btn-primary btn-large">
                    Login to Start Detecting
                </a>
            <?php endif; ?>
            <a href="./index.php" class="btn btn-outline btn-large">← Back to Home</a>
        </div>
    </div>
</main>

<script>
document.getElementById("start_detect").addEventListener("click", function(e) {
    e.preventDefault();

    fetch("http://localhost:5000/activate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ active: true })
    })
    .then(res => {
        if (!res.ok) throw new Error("Activation failed");
        return res.json();
    })
    .then(() => {
        // ✅ only navigate AFTER request fully completes
        window.location.href = "./camera.php";
    })
    .catch(err => {
        console.error(err);
        alert("Failed: " + err.message);
    });
});
</script>

<?php include './footer.php'; ?>
