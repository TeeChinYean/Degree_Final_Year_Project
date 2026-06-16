<footer class="site-footer">
  <div class="wrap">
    <p>&copy; <?= date('Y') ?> Green Point — Save money, Save Earth</p>
  </div>
</footer>

<style>
#admin-lock-overlay {
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background: rgba(0, 0, 0, 0.85);
    color: white;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 999999;
    font-family: sans-serif;
    display: none;
}
#admin-lock-overlay h1 { font-size: 3rem; margin-bottom: 1rem; color: #ff4d4d; }
#admin-lock-overlay p { font-size: 1.5rem; }
</style>

<div id="admin-lock-overlay">
    <h1>⚠️ UNABLE TO USE</h1>
    <p>This site has been disabled by the Administrator.</p>
</div>

<script>
let assignedStationIp = null;
let localHardwareChecked = false;

function checkHardwareAndPoll() {
    // 1. Try checking if there is a local AI engine running on this machine (localhost:5000)
    fetch("http://localhost:5000/system_status")
        .then(res => res.json())
        .then(data => {
            if (data.station_ip && data.site_id) {
                assignedStationIp = data.station_ip;
                const overlay = document.getElementById("admin-lock-overlay");
                overlay.style.display = (data.admin_enabled === false) ? "flex" : "none";

                // Auto-bind user to this hardware station
                if (!localHardwareChecked) {
                    localHardwareChecked = true;
                    fetch("./api_station.php?action=assign_user", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ user_id: <?= intval($_SESSION['user_id'] ?? 0) ?>, station_id: data.site_id })
                    });
                }
            }
        })
        .catch(() => {
            // 2. Fallback: if not running on station PC (e.g. mobile phone), poll assigned IP
            const targetIp = assignedStationIp || window.location.hostname;
            fetch(`http://${targetIp}:5000/system_status`)
                .then(res => res.json())
                .then(data => {
                    const overlay = document.getElementById("admin-lock-overlay");
                    overlay.style.display = (data.admin_enabled === false) ? "flex" : "none";
                })
                .catch(() => {});
        });
}

// Initial fetch of user's assigned station IP
fetch("./api_station.php?action=my_station")
    .then(res => res.json())
    .then(data => {
        if (data.assigned && data.station_ip) {
            assignedStationIp = data.station_ip;
        }
        checkHardwareAndPoll();
        setInterval(checkHardwareAndPoll, 2000);
    })
    .catch(() => {
        checkHardwareAndPoll();
        setInterval(checkHardwareAndPoll, 2000);
    });
</script>

</body>
</html>
