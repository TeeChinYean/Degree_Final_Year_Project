<?php
require './config.php';
session_start();

// Redirect if already logged in
if (!empty($_SESSION['user_id'])) {
    header('Location: ./dashboard.php');
    exit;
}

$err = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username']);
    $password = $_POST['password'];

    $stmt = $pdo->prepare('SELECT User_id, password FROM users WHERE User_name = ?');
    $stmt->execute([$username]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($user && password_verify($password, $user['password'])) {
        $_SESSION['user_id'] = $user['User_id'];
        $_SESSION['user'] = $user['User_name'];
        header('Location: ./dashboard.php');
        exit;
    } else {
        $err = 'Invalid username or password.';
    }
}

include './header.php';
?>

<main class="auth-container">
    <div class="auth-card">
        <div class="auth-header">
            <h1>Welcome Back</h1>
            <p class="auth-subtitle">Sign in to your Green Point account</p>
        </div>

        <?php if ($err): ?>
            <div class="alert error">
                <strong>Error:</strong> <?= htmlspecialchars($err) ?>
            </div>
        <?php endif; ?>

        <form method="post" class="auth-form">
            <div class="form-group">
                <label for="username">Username</label>
                <input 
                    id="username" 
                    name="username" 
                    type="text" 
                    required 
                    autocomplete="username"
                    placeholder="Enter your username"
                    value="<?= isset($_POST['username']) ? htmlspecialchars($_POST['username']) : '' ?>"
                >
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input 
                    id="password" 
                    name="password" 
                    type="password" 
                    required 
                    autocomplete="current-password"
                    placeholder="Enter your password"
                >
            </div>

            <button type="submit" class="btn btn-primary btn-block btn-large">Sign In</button>
        </form>

        <div class="auth-footer">
            <p>Don't have an account? <a href="./register.php">Create one here</a></p>
            <p><a href="./index.php">← Back to Home</a></p>
        </div>
    </div>
</main>

<?php include './footer.php'; ?>
