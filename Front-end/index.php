<?php
require './config.php';
session_start();

// Ensure username is available for the homepage greeting
if (!empty($_SESSION['user_id']) && empty($_SESSION['user'])) {
  $stmt = $pdo->prepare('SELECT User_name FROM users WHERE User_id = ?');
  $stmt->execute([(int)$_SESSION['user_id']]);
  $name = $stmt->fetchColumn();
  if ($name) {
    $_SESSION['user'] = $name;
  }
}

// Handle form submission
$success = $error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (empty($_SESSION['user_id'])) {
        // User not logged in
        header('Location: ./login.php');
        exit;
    }

    $user_id = $_SESSION['user_id'];
    $message = trim($_POST['message'] ?? '');

    if ($message !== '') {
        $stmt = $pdo->prepare("INSERT INTO contact_messages (User_id, Message, status, created_at) VALUES (?, ?, 0, NOW())");
        $stmt->execute([$user_id, $message]);
        $success = '✅ Your message has been sent successfully!';
    } else {
        $error = '⚠️ Message cannot be empty.';
    }
}
?>
<?php include './header.php'; ?>

<main class="main-container">

  <!-- HERO SECTION -->
  <section class="hero-section">
    <div class="hero-content">
      <h1>Green Point</h1>
      <p class="tagline">Save money, Save Earth</p>
      <p>Transform your recycling into rewards with AI-powered detection</p>

      <div class="cta-group">
        <?php if(isset($_SESSION['user_id'])): ?>
            <div class="btn-group">
              <a class="btn btn-primary btn-large" href="./dashboard.php">Go to Dashboard</a>
              <form method="post" action="start_detect_setup.php" style="margin: 0;">
                <button class="btn btn-outline btn-large" name="start_detection" type="submit">
                  Start Detecting Items
                </button>
              </form>
          </div>
        <?php else: ?>
          <div class="btn-group">
            <a class="btn btn-primary btn-large" href="./login.php">Login / Scan QR</a>
            <a class="btn btn-outline btn-large" href="./register.php">Create Account</a>
          </div>
        <?php endif; ?>
      </div>
    </div>
  </section>

  <!-- FEATURES SECTION -->
  <section class="info-section">
    <div class="info-card">
      <h2>♻️ Recyclable Items</h2>
      <img src="../img/bin.png" alt="Recycling Types" class="responsive-img">
      <ul>
        <li><strong>Plastic</strong> — bottles, containers, packaging</li>
        <li><strong>Metal</strong> — aluminum cans, tin containers</li>
        <li><strong>Paper</strong> — cardboard, newspapers, packaging</li>
      </ul>
    </div>

    <div class="info-card">
      <h2>💡 Recycling Tips</h2>
      <p>Clean items thoroughly before recycling. Soap removes contamination more effectively than water alone, ensuring your items are properly processed and you earn maximum points!</p>
      <p style="margin-top: 1rem; font-size: 0.95rem; color: var(--gray-500);">
        <strong>Pro tip:</strong> Remove labels and caps when possible for better recycling efficiency.
      </p>
    </div>
  </section>

  <!-- ABOUT SECTION -->
  <section id="about" class="about-section">
    <div class="about-content">
      <h2>About Green Point</h2>
      <p>
        Green Point is an innovative reward-based recycling system powered by advanced AI image recognition technology. 
        Our mission is to make recycling rewarding and accessible for everyone.
      </p>
      <p style="margin-top: 1.5rem;">
        By combining cutting-edge technology with environmental consciousness, we increase recycling participation, 
        improve traceability, and incentivize sustainable behavior through our point-based reward system. 
        Join thousands of users making a positive impact on our planet while earning rewards!
      </p>
    </div>
  </section>

  <!-- CONTACT SECTION -->
  <section id="contact" class="contact-section">
    <div class="form-section">
      <h1>Get in Touch</h1>
      <p>Have questions or feedback? We'd love to hear from you!</p>
      <?php if (isset($success) && $success): ?>
        <div class="alert success"><?= htmlspecialchars($success) ?></div>
      <?php elseif (isset($error) && $error): ?>
        <div class="alert error"><?= htmlspecialchars($error) ?></div>
      <?php endif; ?>
      <form method="post" class="styled-form">
        <div class="form-group">
          <label for="message">Your Message</label>
          <textarea id="message" name="message" rows="6" placeholder="Tell us what's on your mind..." required></textarea>
        </div>
        <button type="submit" class="btn btn-primary btn-block">Send Message</button>
      </form>
    </div>
  </section>

</main>

<?php include './footer.php'; ?>
