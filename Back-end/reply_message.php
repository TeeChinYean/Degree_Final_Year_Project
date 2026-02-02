<?php
require 'includes/db.php';
require '../phpmailer/src/PHPMailer.php';
require '../phpmailer/src/SMTP.php';
require '../phpmailer/src/Exception.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $message_id = (int)$_POST['message_id'];
    $email = $_POST['email'];
    $reply = trim($_POST['reply']);

    if ($message_id && $reply !== '') {
        // Update status in DB
        $stmt = $pdo->prepare("UPDATE contact_messages SET Status=1 WHERE Contact_Id=?");
        $stmt->execute([$message_id]);

        // Send email
        $mail = new PHPMailer(true);
        try {
            $mail->isSMTP();
            $mail->Host = 'smtp.gmail.com'; // ✅ Change to your SMTP server
            $mail->SMTPAuth = true;
            $mail->Username = 'GreenSite370@gmail.com'; // ✅ Your email
            $mail->Password = 'dkmm tdfe tzxj fmts'; // ✅ App-specific password
            $mail->SMTPSecure = 'tls';
            $mail->Port = 587;

            $mail->setFrom('GreenSite370@gmail.com', 'GreenPoint Admin');#gmail password: Plm!1234
            $mail->addAddress($email);
            $mail->isHTML(true);
            $mail->Subject = 'Reply from GreenPoint Support';
            $mail->Body = nl2br(htmlspecialchars($reply));

            $mail->send();
            header('Location: manage_messages.php?sent=1');
            exit;
        } catch (Exception $e) {
            header('Location: manage_messages.php?error=mail');
            exit;
        }
    }
}
?>
