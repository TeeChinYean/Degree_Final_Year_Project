<?php
session_start();
if (empty($_SESSION['Admin_id'])) {
    header('Location: login.php');
    exit;
}

require 'includes/header.php';
?>
<main style="max-width:1100px;margin:36px auto;padding:20px">
  <h2 style="background:#0f5b63;color:#fff;padding:10px 14px;border-radius:6px;margin-bottom:16px;text-align:center">
    Recycling Statistics Charts
  </h2>

  <div style="display:flex;gap:20px;flex-wrap:wrap;justify-content:center">
    <div style="flex:1;min-width:320px;background:#fff;padding:16px;border-radius:8px;box-shadow:0 0 8px rgba(0,0,0,0.1)">
      <h3 style="text-align:center;color:#0f5b63">Recycling Type Distribution</h3>
      <canvas id="pieChart" width="400" height="300"></canvas>
    </div>

    <div style="flex:1;min-width:320px;background:#fff;padding:16px;border-radius:8px;box-shadow:0 0 8px rgba(0,0,0,0.1)">
      <h3 style="text-align:center;color:#0f5b63">Monthly Breakdown</h3>
      <canvas id="barChart" width="400" height="300"></canvas>
    </div>
  </div>

  <div style="margin-top:32px;background:#fff;padding:16px;border-radius:8px;box-shadow:0 0 8px rgba(0,0,0,0.1)">
    <h3 style="text-align:center;color:#0f5b63">Trend Over Time</h3>
    <canvas id="lineChart" width="1000" height="300"></canvas>
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
