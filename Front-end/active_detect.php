<?php
// Corrected JSON reading logic
$json_data = file_get_contents('data.json');
$data = json_decode($json_data, true);

// Check JSON validity ONCE before looping
if (json_last_error() !== JSON_ERROR_NONE || !is_array($data)) {
    $data = []; // Fallback to empty array
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Active Detect</title>
    <link rel="stylesheet" href="../style/style.css">
</head>
<body>
    <?php include './header.php'; ?>
    
    <main class="container">
        <?php foreach ($data as $item): ?>
            <p>User ID: <?php echo htmlspecialchars($item['user_id']); ?></p>
        <?php endforeach; ?>

        <button id="detectBtn" class="btn">Start Active Detect</button>
        <div id="status" style="color:yellow;">Status: Idle</div>
        <pre id="result" style="color:white; font-size: 12px;"></pre>
    </main>

    <script>
    document.getElementById('detectBtn').addEventListener('click', function() {
        const btn = this;
        const statusDiv = document.getElementById('status');
        const resultPre = document.getElementById('result');

        btn.disabled = true;
        statusDiv.innerText = "Status: Running Python script...";

        fetch('run_task.php', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                statusDiv.innerText = "Status: " + data.status;
                resultPre.innerText = data.output;
            })
            .catch(err => {
                statusDiv.innerText = "Status: Connection Error";
                console.error(err);
            })
            .finally(() => {
                btn.disabled = false;
            });
    });
    </script>
</body>
</html>