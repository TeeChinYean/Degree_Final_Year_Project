<?php
$cmd = isset($_GET['cmd']) ? $_GET['cmd'] : '';

if ($cmd == 'start_detect') {
    // Run your YOLO or detection-related backend logic here
    echo "<h3>Object detection started...</h3>";
    // Example: call Python script or update DB
    // shell_exec("python detect.py"); 
}
elseif ($cmd == 'generate_report') {
    echo "<h3>Generating report...</h3>";
    // Example: call PHP report generation
    // include 'report.php';
}
else {
    echo "<h3>Invalid command</h3>";
}
?>
