<?php
// Simple demo analyze - in production you'd call an ML model or external API.
// This demo inspects the uploaded filename or returns a random selection.
require './config.php';
session_start();
$user_id = $_SESSION['user_id'] ?? null;
if($_SERVER['REQUEST_METHOD']==='POST' && isset($_FILES['photo'])){
    $f = $_FILES['photo'];
    $name = basename($f['name']);
    $tmp = $f['tmp_name'];
    $dest_dir = 'uploads';
    if(!is_dir($dest_dir)) mkdir($dest_dir,0755,true);
    $dest = $dest_dir.'/'.time().'_'.preg_replace('/[^a-z0-9\.\-_]/i','_', $name);
    move_uploaded_file($tmp,$dest);

    // naive keyword mapping
    $mapping = [
      'bottle'=>['type'=>'Plastic','points'=>2],
      'can'=>['type'=>'Metal','points'=>3],
      'paper'=>['type'=>'Paper','points'=>1],
      'glass'=>['type'=>'Glass','points'=>4],
    ];
    $found = null;
    foreach($mapping as $k=>$v){
        if(stripos($name,$k)!==false){ $found = $v; break; }
    }
    if(!$found){
        // fallback: pick the most common type
        $found = $mapping['paper'];
    }
    $count = 1;
    $points = $found['points'] * $count;
    if($user_id){
        $pdo->prepare('INSERT INTO recycling (user_id,type,count,points,created_at) VALUES (?,?,?,?,NOW())')
            ->execute([$user_id,$found['type'],$count,$points]);
        $pdo->prepare('UPDATE users SET balance = balance + ? WHERE id=?')->execute([$points,$user_id]);
    }
    header('Content-Type: application/json');
    echo json_encode(['status'=>'ok','detected'=>$found['type'],'points'=>$points,'uploaded'=>$dest]);
    exit;
}
header('Location: ./login.php');
?>