<?php
require './config.php';
session_start();
unset($_SESSION['confirmed_once']);
?>
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Item Detection - Green Point</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="../style/camera_page.css">
</head>
<body>
<?php include './header.php'; ?>
<div class="container">
    <!-- Stream Section -->
    <div class="stream-container">
        <img id="video" src="http://localhost:5000/video" width="640" height="480">
    </div>

    <!-- Data List Section -->
    <div class="data-container">
        <div id="result"></div>
        <button id="confirmBtn" onclick="finishDetect()">Confirm Result?</button>
    </div>
    
</div>

<?php if (isset($_SESSION['insert_success']) && $_SESSION['insert_success'] === 'success'): ?>
<script>
    alert("Insert success");
</script>
<?php unset($_SESSION['insert_success']); endif; ?>

<div id="back-button" class="btn-container" style="margin-top:16px;">
        <button class="btn" onclick="Back()">Back</button>
    </div>
<?php include './footer.php'; ?>

<script>
const evtSource = new EventSource("http://localhost:5000/word_event");
let detectionResults = [];

evtSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    detectionResults.push({
        item: data.item,
        weight: data.weight
    });

    // Create new item
    const p = document.createElement("p");
    p.innerText = `${data.item} - ${data.weight} g`;

    // Append to result container
    document.getElementById("result").appendChild(p);
    p.scrollIntoView({behavior: "smooth"});
};

evtSource.onerror = function(err) {
    console.error("SSE error", err);
};

// Example button event listeners
document.getElementById("startStopBtn").addEventListener("click", () => {
    fetch("http://localhost:5000/toggle_detect"); // your Flask endpoint
});

document.getElementById("confirmBtn").addEventListener("click", () => {
    fetch("http://localhost:5000/confirm_result"); // your Flask endpoint
});

function finishDetect() {
    if (detectionResults.length === 0) {
        alert("No items detected yet.");
        return;
    }

    fetch('process_detection.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(detectionResults)
    })
    .then(response => {
        if (response.ok) {
            window.location.href = 'detection_result.php';
        } else {
            alert("Failed to save detection data.");
        }
    })
    .catch(err => console.error("Error:", err));
}

function Back() {
    window.history.back();
}
</script>

</body>
</html>
