<?php
require './config.php';
session_start();
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Green Point — Save money, Save Earth</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link rel="stylesheet" href="../style/style.css">
</head>
<body>
<?php include './header.php'; ?>

<main class="container">

  <!-- Main Content -->
  <section class="hero" style="text-align:center; padding:48px 0;color:white;">
    <h4>Green Point</h4>
    <h2 class="tagline">Save money, Save Earth</h2>
    <div class="cta-row">
      <?php if(isset($_SESSION['user_id'])): ?>
        <div style="display:flex;flex-direction:column;gap:16px;align-items:center;">
          <div>
            <h3 style="color:black;">Welcome, <?= htmlspecialchars($_SESSION['user']) ?>!</h3>
            <a class="btn" href="./dashboard.php">Go to Dashboard</a>
            <a class="btn outline" href="./logout.php">Logout</a>
          </div>
          <div>
            <form method="post" action="start_detect_setup.php">
              <button class="btn" id="activate-btn" name="start_detection">Start Detecting Items</button>
            </form>
          </div>
          
      </div>
        
      <?php else: ?>
        <a class="btn" href="./login.php">Login / Scan QR</a>
        <a class="btn outline" href="./register.php">Register</a>
      <?php endif; ?>
    </div>
  </section>

  <section class="features" style="display:flex;flex-direction:column;gap:32px;max-width:80%;margin:0 auto;padding:24px 0;">
      <!-- Proceeds Section -->
    <article class="proceeds" style="background-color:aquamarine; border-style:solid; border-radius:4px; padding:16px;">
      <h2>How it proceeds</h2>
      <ol>
        <li><strong>User Interaction</strong> – Login or register by scanning a QR code at the recycling station (or use account).</li>
        <li><strong>Item Detection</strong> – The camera takes a photo, the system analyses the item type and counts quantity.</li>
        <li><strong>Point Calculation</strong> – Each recognized item is assigned green points based on material and weight.</li>
        <li><strong>Rewards</strong> – Points are added to the user balance and can be redeemed later.</li>
      </ol>
    </article>

        <!--Recycle Item Types Section -->
    <article class="recycle-types" style="background-color:aquamarine;  border-style:solid; border-radius:4px; padding:16px;">
      <img src="../img/recycle_type.jpg" alt="Recycling" style="max-width:80%;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.1);margin-top:16px;">
      <h2>Recycle Item Types</h2>
      <ul>
        <li>Plastic — bottles, containers, cups</li>
        <li>Metal — aluminum cans, tin cans</li>
        <li>Paper — newspapers, cardboard, packaging</li>
        <li>Glass — bottles, jars</li>
      </ul>
    </article>

        <!-- Tips Section -->
    <article class="tips" style="background-color:aquamarine;  border-style:solid; border-radius:4px; padding:16px;">
      <h2>Tips</h2>
      <p>Always clean items before recycling — soap and water are more effective than water alone in removing germs.</p>
    </article>
  </section>
</main>

<!-- Footer -->
<?php include './footer.php'; ?>
</body>
</html>
