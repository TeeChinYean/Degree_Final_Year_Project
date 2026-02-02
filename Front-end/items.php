<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Recycle Item Types - Green Point</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="../style/style.css">
</head>
<body>
<?php
require './config.php';
include './header.php';
$stmt = $pdo->query('SELECT * FROM item_types ');
$items = $stmt->fetchAll();
?>
<div id="container">
  <div class="wrap" style="padding:24px 0">
    <h1>Recycle Item Types</h1>
    <table>
      <tr><th>Material</th><th>Example Items</th><th>Points per item</th></tr>
      <?php foreach($items as $it): ?>
        <tr>
          <td><?php echo htmlspecialchars($it['Type']); ?></td>
          <td><?php echo htmlspecialchars($it['Examples']); ?></td>
          <td><?php echo (int)$it['Points']; ?></td>
        </tr>
      <?php endforeach; ?>
    </table>  
  </div>
  <div id="detect-button" class="btn-outline">
    <form method="post" action="start_detect_setup.php">
      <button class="btn" id="activate-btn" name="start_detection">Start Detecting Items</button>
    </form>
  </div>
  <div id="back-button" class="btn-container" style="margin-top:16px;">
    <button class="btn" onclick="Back()">Back</button>
  </div>
</div>
<?php include './footer.php'; ?>
</body>
</html>

<script>
document.getElementById("activate-btn").addEventListener("click", function(event) {
    event.preventDefault(); 
    
    // 2. CHANGED URL to point to Python (Port 5000)
    // The request must go to the Flask server, not the PHP server.
    fetch("http://localhost:5000/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: true })
    })
    .then(response => {
        console.log("Wake up command sent");
        // 3. Navigate ONLY after the request is sent
        window.location.href = './camera.php';
    })
    .catch(err => {
        console.error("Error connecting to Python:", err);
        // Even if Python is down, we still go to the camera page so the user isn't stuck
        window.location.href = './camera.php';
    });
});

function Back() {
    window.history.back();
}
</script>