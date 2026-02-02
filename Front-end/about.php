<?php include './header.php'; ?>
<link rel="stylesheet" href="../style/style.css">
<div class="wrap" style="padding:24px 0">
  <h1>About Green Point</h1>
  <p>Green Point is a rewards-based recycling system that uses camera-based item recognition to streamline recycling and reward users with points. It aims to solve real world problems: increase recycling rates, make recycling traceable, and incent users with tangible rewards.</p>
</div>
<div id="back-button" class="btn-container" style="margin-top:16px;">
        <button class="btn" onclick="Back()">Back</button>
    </div>
<?php include './footer.php'; ?>
<script>
  function Back() {
    window.history.back();
  }
</script>
