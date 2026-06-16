<?php
session_start();

unset($_SESSION['confirmed_once']);
unset($_SESSION['detectionResults']); // optional, but clean

header('Location: camera.php');
exit;
