<?php
require './config.php';
session_start();

// Redirect if already logged in
if (!empty($_SESSION['user_id'])) {
    header('Location: ./dashboard.php');
    exit;
}

$error = '';
$success = false;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = trim($_POST['email']);
    $user_name = trim($_POST['User_name']);
    $password = $_POST['password'];
    $confirm_password = $_POST['confirm_password'] ?? '';

    // Validation
    if (empty($user_name) || empty($email) || empty($password)) {
        $error = "All fields are required.";
    } elseif ($password !== $confirm_password) {
        $error = "Passwords do not match.";
    } elseif (strlen($password) < 6) {
        $error = "Password must be at least 6 characters long.";
    } else {
        // Check for duplicate email
        $checkStmt = $pdo->prepare('SELECT User_id FROM users WHERE User_email = ?');
        $checkStmt->execute([$email]);
        
        if ($checkStmt->fetch()) {
            $error = "This email is already registered.";
        } else {
            // Check for duplicate username
            $checkUserStmt = $pdo->prepare('SELECT User_id FROM users WHERE User_name = ?');
            $checkUserStmt->execute([$user_name]);
            
            if ($checkUserStmt->fetch()) {
                $error = "This username is already taken.";
            } else {
                $hashed_password = password_hash($password, PASSWORD_DEFAULT);

                $insertStmt = $pdo->prepare(
                    'INSERT INTO users 
                    (User_name, Password, User_email, status, balance, date)
                    VALUES (?, ?, ?, 0, 0, NOW())'
                );

                if ($insertStmt->execute([$user_name, $hashed_password, $email])) {
                    // Auto-login after registration
                    $newUserStmt = $pdo->prepare('SELECT User_id FROM users WHERE User_email = ?');
                    $newUserStmt->execute([$email]);
                    $newUser = $newUserStmt->fetch();
                    
                    $_SESSION['user_id'] = $newUser['User_id'];
                    $_SESSION['user'] = $user_name;
                    header('Location: ./dashboard.php');
                    exit;
                } else {
                    $error = "Registration failed. Please try again.";
                }
            }
        }
    }
}

include './header.php';
?>

<main class="auth-container">
    <div class="auth-card">
        <div class="auth-header">
            <h1>Create Account</h1>
            <p class="auth-subtitle">Join Green Point and start earning rewards</p>
        </div>

        <?php if ($error): ?>
            <div class="alert error">
                <strong>Error:</strong> <?= htmlspecialchars($error) ?>
            </div>
        <?php endif; ?>

        <form method="post" class="auth-form">
            <div class="form-group">
                <label for="User_name">Username</label>
                <input 
                    id="User_name" 
                    name="User_name" 
                    type="text" 
                    required 
                    autocomplete="username"
                    placeholder="Choose a username"
                    value="<?= isset($_POST['User_name']) ? htmlspecialchars($_POST['User_name']) : '' ?>"
                >
            </div>

            <div class="form-group">
                <label for="email">Email Address</label>
                <input 
                    id="email" 
                    name="email" 
                    type="email" 
                    required 
                    autocomplete="email"
                    placeholder="your.email@example.com"
                    value="<?= isset($_POST['email']) ? htmlspecialchars($_POST['email']) : '' ?>"
                >
            </div>

            <div class="form-group">
                <label for="password">Password</label>
                <input 
                    id="password" 
                    name="password" 
                    type="password" 
                    required 
                    autocomplete="new-password"
                    placeholder="At least 6 characters"
                    minlength="6"
                >
                <small class="form-hint">Minimum 6 characters</small>
            </div>

            <div class="form-group">
                <label for="confirm_password">Confirm Password</label>
                <input 
                    id="confirm_password" 
                    name="confirm_password" 
                    type="password" 
                    required 
                    autocomplete="new-password"
                    placeholder="Re-enter your password"
                    minlength="6"
                >
            </div>

            <button type="submit" class="btn btn-primary btn-block btn-large">Create Account</button>
        </form>

        <div class="auth-footer">
            <p>Already have an account? <a href="./login.php">Sign in here</a></p>
            <p><a href="./index.php">← Back to Home</a></p>
        </div>
    </div>
</main>

<?php include './footer.php'; ?>
