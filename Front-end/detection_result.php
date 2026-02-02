<?php
session_start();

if (!isset($_SESSION['detectionResults']) || empty($_SESSION['detectionResults'])) {
    header("Location: camera.php");
    exit();
}
unset($_SESSION['confirmed_once']);
$data = $_SESSION['detectionResults'];

$itemMap = [
    'plastic-bottle' => 1,
    'can'      => 2,
    'Glass Bottle'   => 3,
    'paper'          => 4,
    'Steel Can'      => 5,
    'Wired'          => 6
];

###########################################################################
//sum each type weight, set if plastic, then point is 1, continue...
//at the end total weight, and points
//point should be integer
$totalWeight = 0;
$totalPoints = 0;

foreach ($data as $entry) {
    $itemName = trim($entry['item']);
    $weight   = (int)$entry['weight'];

    if (!isset($itemMap[$itemName])) {
        continue;
    }

    $totalWeight += $weight;

    switch ($itemMap[$itemName]) {
        case 1: $pointsPerItem = 1; break;
        case 2: $pointsPerItem = 2; break;
        case 3: $pointsPerItem = 3; break;
        case 4: $pointsPerItem = 1; break;
        case 5: $pointsPerItem = 2; break;
        case 6: $pointsPerItem = 4; break;
        default: $pointsPerItem = 0;
    }

    $rawPoints = ($weight / 100) * $pointsPerItem;
    $totalPoints += (int) round($rawPoints);
}

?>

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Detection Result</title>
</head>
<body>

<h2>Detection Results</h2>
<div style="display:flex; flex-direction:row;">
    <div style="flex-grow: 1">
        <table border="1">
            <tr>
                <th>Item</th>
                <th>Weight (g)</th>
            </tr>
            <?php foreach ($data as $entry): ?>
            <tr>
                <td><?= htmlspecialchars($entry['item']) ?></td>
                <td><?= htmlspecialchars($entry['weight']) ?></td>
            </tr>
            <?php endforeach; ?>
        </table>
    </div>
    <div style="flex-grow: 2">
        <table border="1">
            <tr>
                <th>Total Weight (g)</th>
                <td><?= $totalWeight ?></td>
                <th>Total Points</th>
                <td><?= $totalPoints ?></td>
            </tr>
            <tr>
                <form action="confirm_result.php" method="post">
                    <input type="hidden" name="total_weight" value="<?= $totalWeight ?>">
                    <input type="hidden" name="total_points" value="<?= $totalPoints ?>">
                    <button type="submit" name="action" value="confirm">Confirm</button>
                    <button type="submit" name="action" value="cancel">Cancel</button>
                </form>
            </tr>
        </table>
    </div>
</div>







<script>
function confirmResult() {
    fetch("confirm_result.php", { method: "POST" })
        .then(() => window.location.href = "camera.php");
}

function deleteResult() {
    fetch("delete_result.php", { method: "POST" })
        .then(() => window.location.href = "camera.php");
}
</script>

</body>
</html>


<!-- <?php
session_start();

// Handle AJAX delete request before any redirects
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'delete') {
    unset($_SESSION['detectionResults']);
    // return simple response
    echo 'deleted';
    exit;
}

if (!isset($_SESSION['detectionResults'])) {
    header("Location: camera.php");
    exit();
}

$data = $_SESSION['detectionResults'];
?>

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Detection Result</title>
</head>
<body>

<h2>Detection Results</h2>

<table border="1">
    <tr>
        <th>Item</th>
        <th>Weight (g)</th>
    </tr>
    <?php foreach ($data as $entry): ?>
    <tr>
        <td><?= htmlspecialchars($entry['item']) ?></td>
        <td><?= htmlspecialchars($entry['weight']) ?></td>
    </tr>
    <?php endforeach; ?>
</table>
<button onclick="confirmResult()">Confirm Result</button>
<button onclick="deleteResult()">Delete Result</button>

<script>
function confirmResult() {
    fetch("confirm_result.php", { method: "POST" })
        .then(() => window.location.href = "camera.php");
}

function deleteResult() {
    fetch("detection_result.php", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "action=delete"
    }).then(() => window.location.href = "camera.php");
}
</script>

</body>
</html> -->
