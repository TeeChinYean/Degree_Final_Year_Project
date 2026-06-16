"""
setup.py  — GreenPoint Station First-Time Setup
Run this ONCE on each new station before starting main_system.exe

Steps:
 1. Input station name and (optionally) a custom Site ID
 2. Auto-detect local IP (Tailscale preferred)
 3. Send application to admin server → wait for approval
 4. Write site_config.json
"""

import os
import sys
import json
import uuid
import socket
import time
import requests

# ── Config ─────────────────────────────────────────────────────────────────
ADMIN_SERVER     = "http://100.83.94.86"
APPLY_URL        = f"{ADMIN_SERVER}/Front-end/api_station.php?action=apply"
STATUS_URL       = f"{ADMIN_SERVER}/Front-end/api_station.php?action=status"
CONFIG_FILENAME  = "site_config.json"
POLL_INTERVAL    = 10   # seconds between approval checks
RTSP_PORT        = 8554
DEFAULT_FLASK_PORT = 5000

# ── Helpers ────────────────────────────────────────────────────────────────
def get_local_ip() -> str:
    """Return the best-guess local/Tailscale IP of this machine."""
    # Try Tailscale range first (100.x.x.x)
    try:
        hostname = socket.gethostname()
        addrs = socket.getaddrinfo(hostname, None)
        for addr in addrs:
            ip = addr[4][0]
            if ip.startswith('100.'):
                return ip
    except Exception:
        pass

    # Fallback: connect to 8.8.8.8 and see which interface is used
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def load_existing_config() -> dict:
    if os.path.exists(CONFIG_FILENAME):
        try:
            with open(CONFIG_FILENAME, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(cfg: dict) -> None:
    with open(CONFIG_FILENAME, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"\n[OK] Configuration saved to: {os.path.abspath(CONFIG_FILENAME)}")


def print_banner():
    print("=" * 60)
    print("   GreenPoint Station Setup")
    print("   Admin Server:", ADMIN_SERVER)
    print("=" * 60)


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    print_banner()

    existing = load_existing_config()

    # ── Step 1: Site ID ───────────────────────────────────────────────────
    default_id = existing.get("SITE_ID") or f"Site_{uuid.uuid4().hex[:6].upper()}"
    print(f"\nStep 1/4 — Site ID")
    print(f"  Default: {default_id}")
    raw = input("  Enter Site ID (press Enter to use default): ").strip()
    site_id = raw if raw else default_id

    # ── Step 2: Station Name ──────────────────────────────────────────────
    default_name = existing.get("STATION_NAME") or site_id
    print(f"\nStep 2/4 — Station Name (shown in admin monitor)")
    print(f"  Default: {default_name}")
    raw = input("  Enter Station Name (press Enter to use default): ").strip()
    station_name = raw if raw else default_name

    # ── Step 3: IP detection ──────────────────────────────────────────────
    detected_ip = get_local_ip()
    print(f"\nStep 3/4 — Station IP")
    print(f"  Detected: {detected_ip}")
    raw = input("  Enter IP to register (press Enter to use detected): ").strip()
    station_ip = raw if raw else detected_ip

    # ── Step 4: Camera index ──────────────────────────────────────────────
    default_cam = existing.get("CAMERA_INDEX", 0)
    print(f"\nStep 4/4 — Camera Index (0 = first camera, 1 = second, etc.)")
    print(f"  Default: {default_cam}")
    raw = input("  Enter camera index (press Enter to use default): ").strip()
    try:
        camera_index = int(raw) if raw else default_cam
    except ValueError:
        camera_index = default_cam

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print("  Summary:")
    print(f"    Site ID      : {site_id}")
    print(f"    Station Name : {station_name}")
    print(f"    Station IP   : {station_ip}")
    print(f"    Camera Index : {camera_index}")
    print(f"    Admin Server : {ADMIN_SERVER}")
    print("─" * 60)
    confirm = input("\nSend application to admin? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Setup cancelled.")
        sys.exit(0)

    # ── Send application ──────────────────────────────────────────────────
    print(f"\n[...] Sending application to {APPLY_URL}")
    try:
        resp = requests.post(APPLY_URL, json={
            "site_id":      site_id,
            "station_name": station_name,
            "station_ip":   station_ip,
            "rtsp_port":    RTSP_PORT,
        }, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        status = result.get("status", "unknown")
        print(f"[OK] Server response: {status}")
    except requests.RequestException as e:
        print(f"[ERROR] Could not reach admin server: {e}")
        print("       Check that admin server is running and reachable.")
        sys.exit(1)

    # Save config immediately regardless of approval status
    cfg = {
        "SITE_ID":        site_id,
        "STATION_NAME":   station_name,
        "STATION_IP":     station_ip,
        "ADMIN_SERVER_URL": f"{ADMIN_SERVER}:5001",
        "CAMERA_INDEX":   camera_index,
        "RTSP_PORT":      RTSP_PORT,
    }
    save_config(cfg)

    # ── Poll for approval ─────────────────────────────────────────────────
    if status == 'approved':
        print("\n[✓] Station is already approved! You may run main_system.exe.")
        return

    print(f"\n[⏳] Application submitted. Waiting for admin approval...")
    print(f"     (Checking every {POLL_INTERVAL} seconds — press Ctrl+C to exit and check later)\n")

    try:
        while True:
            time.sleep(POLL_INTERVAL)
            try:
                r = requests.get(STATUS_URL, params={"site_id": site_id}, timeout=5)
                data = r.json()
                current = data.get("status", "")
                print(f"  [{time.strftime('%H:%M:%S')}] Status: {current}", end='\r')

                if current == 'approved':
                    print(f"\n\n[✓] APPROVED! Station '{station_name}' is now active.")
                    print("    You can now run main_system.exe.")
                    break
                elif current == 'rejected':
                    print(f"\n\n[✗] Application REJECTED by admin.")
                    print("    Contact admin or re-run setup.py to reapply.")
                    break
            except Exception:
                print("  [!] Could not check status — will retry...")
    except KeyboardInterrupt:
        print("\n\n[i] Exited. Run setup.py again to check approval status.")
        print("    Your config has been saved — no need to re-enter details.")


if __name__ == "__main__":
    main()
