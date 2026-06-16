<?php
session_start();

$json = file_get_contents("php://input");
$data = json_decode($json, true);

if (!$data || !is_array($data)) {
    http_response_code(400);
    exit("Invalid data");
}

$_SESSION['detectionResults'] = $data;
http_response_code(200);
?>