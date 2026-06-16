<?php
session_start();
if (empty($_SESSION['Admin_id'])) {
    header('Location: login.php');
    exit;
}

require 'includes/header.php';
?>
<main class="admin-main">
  <h1 class="admin-title">Recycling Statistics</h1>
  <p class="admin-subtitle">Charts update automatically from recent submissions.</p>

  <div class="admin-card" style="margin-top:16px;">
    <div class="admin-card-header">Charts</div>
    <div class="admin-card-body">
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;">
        <div class="admin-card" style="box-shadow:var(--shadow-sm);">
          <div class="admin-card-header">Type Distribution</div>
          <div class="admin-card-body">
            <canvas id="pieChart" width="400" height="300"></canvas>
          </div>
        </div>

        <div class="admin-card" style="box-shadow:var(--shadow-sm);">
          <div class="admin-card-header">Monthly Breakdown</div>
          <div class="admin-card-body">
            <canvas id="barChart" width="400" height="300"></canvas>
          </div>
        </div>
      </div>

      <div class="admin-card" style="margin-top:16px;box-shadow:var(--shadow-sm);">
        <div class="admin-card-header">Trend Over Time</div>
        <div class="admin-card-body">
          <canvas id="lineChart" width="1000" height="300"></canvas>
        </div>
      </div>
    </div>
  </div>
</main>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
async function fetchData() {
  const resp = await fetch('chart_data.php');
  return await resp.json();
}

(async () => {
  const data = await fetchData();
  if (data.error) {
    alert('Session expired. Please log in again.');
    location.href = 'login.php';
    return;
  }

  const types = data.types;
  const totals = types.map(t => data.totals[t] || 0);
  const months = data.months;

  // PIE CHART
  new Chart(document.getElementById('pieChart'), {
    type: 'pie',
    data: {
      labels: types,
      datasets: [{
        data: totals,
        backgroundColor: ['#69d3c5','#6ac1ff','#3b82c4','#ffb86b','#7f6cf5','#4ade80']
      }]
    },
    options: {
      plugins: { legend: { position: 'bottom' } }
    }
  });

  // BAR CHART
  const barDatasets = types.map((t, i) => ({
    label: t,
    data: months.map(m => (data.monthly[m] && data.monthly[m][t]) ? data.monthly[m][t] : 0),
    backgroundColor: `rgba(${80 + i*30}, ${150 - i*15}, ${200 - i*10}, 0.8)`
  }));

  new Chart(document.getElementById('barChart'), {
    type: 'bar',
    data: { labels: months, datasets: barDatasets },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true } },
      plugins: { legend: { position: 'bottom' } }
    }
  });

  // LINE CHART
  const lineDatasets = types.map((t, i) => ({
    label: t,
    data: months.map(m => (data.monthly[m] && data.monthly[m][t]) ? data.monthly[m][t] : 0),
    fill: false,
    tension: 0.3,
    borderColor: `rgba(${90 + i*20}, ${160 - i*20}, ${200 - i*10}, 1)`,
    pointBackgroundColor: '#fff',
    borderWidth: 2
  }));

  new Chart(document.getElementById('lineChart'), {
    type: 'line',
    data: { labels: months, datasets: lineDatasets },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true } },
      plugins: { legend: { position: 'bottom' } }
    }
  });
})();
</script>

<?php require 'includes/footer.php'; ?>
