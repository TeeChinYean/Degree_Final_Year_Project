================================================================================
  Setup & Execution Guide
================================================================================

  TOOLS & VERSIONS
================================================================================

  Tool                  Version         Download
  ──────────────────────────────────────────────────────────────────────────────
  Python                3.12.9 (64-bit) https://www.python.org/downloads/
  Laragon (Full)        6.x             https://laragon.org/download/
    ├─ Apache httpd     2.4.66 Win64    (bundled with Laragon)
    ├─ PHP              8.3.30 Win64    (bundled with Laragon)
    └─ MySQL            8.4.3  Win64    (bundled with Laragon)
  Tailscale VPN         Latest          https://tailscale.com/download
  mediamtx (RTSP)       Latest          https://github.com/bluenviron/mediamtx/releases
  FFmpeg                Release-essentials  https://www.gyan.dev/ffmpeg/builds/

  Python libraries are listed in requirements.txt.
  Install with:  pip install -r requirements.txt

================================================================================
  DATASETS (AI Model Training)
================================================================================

  The detection model was trained using the following Roboflow datasets:

  Class             Dataset / Author                    Link
  ──────────────────────────────────────────────────────────────────────────────
  hand              Human Hand Object Detection          https://universe.roboflow.com/mihai-ciobotaru-mkasd/human-hand-vi8mf
                    by Mihai Ciobotaru

  Aluminium_Can     Detect Can Computer Vision Dataset   https://universe.roboflow.com/add-ejbor/detect-can
                    by add-ejbor

  Aluminium_Can     Can Computer Vision Dataset          https://universe.roboflow.com/project-qynru/can-gcc8l
  (supplementary)   by project-qynru

  paper             Paper Object Detection Dataset       https://universe.roboflow.com/trashdetection-bhjmn/paper-2jpbv
                    by trashdetection

  plastic           Plastic Bottle 2.0                   https://universe.roboflow.com/fyp-li8zz/plastic-bottle-2.0
                    by fyp-li8zz

================================================================================
  PROJECT STRUCTURE
================================================================================

  F:\laragon\www\
  ├── Front-end\           User-facing website (PHP)
  ├── Admin\               Admin dashboard (PHP)
  ├── phpmailer\           Email library
  ├── best_openvino_model\ AI model files (best.xml, best.bin)
  ├── station\             Ready-to-deploy station package (.exe)
  ├── main_system.py       Station detection app (source)
  ├── admin_video_server.py Admin video relay server (source)
  ├── setup.py             Station registration tool (source)
  ├── site_config.json     Station configuration
  ├── requirements.txt     Python dependencies
  └── venv\                Python virtual environment

================================================================================
  SETUP STEPS
================================================================================

  ── A. Web Application (Laragon or XAMPP, prefer Xampp for quick open) ─────────────────────────────────────────────

  1. Install Laragon and start Apache + MySQL.
  2. Place project files in:  F:\laragon\www\
  3. Open Laragon → Database, create a database named  website
  4. Run database migration:  http://localhost/Front-end/run_migration.php
  5. Edit DB credentials in  Front-end/config.php  if needed:
       $db_host = '127.0.0.1';  $db_name = 'website';
       $db_user = 'root';       $db_pass = '';
  6. Access site:  http://localhost/Front-end/   (users)
                   http://localhost/Admin/        (admin)

  ── B. Admin Video Server (Admin PC only) ────────────────────────────────────

  1. Open terminal in  F:\laragon\www\
  2. Activate venv:   venv\Scripts\activate
  3. Run:             python admin_video_server.py
     → Listens on port 5001 (SocketIO) and port 55200 (raw camera TCP)

  ── C. Station Detection System ──────────────────────────────────────────────

  Using pre-built .exe (recommended):
  1. Go to  station\
  2. Run  setup.exe  → enter Station Name, confirm IP, wait for admin approval
  3. After approval, open  station\main_system\  and run  main_system.exe

  Using Python source:
  1. venv\Scripts\activate
  2. python setup.py       ← register station (run once)
  3. python main_system.py ← start detection system

  Station Requirements:
  • Windows 10/11 (64-bit), USB webcam, Intel CPU
  • Tailscale VPN installed and connected
  • mediamtx.exe + ffmpeg.exe in the same folder as main_system.exe

================================================================================
  PORTS USED
================================================================================

  Port   Service
  ─────────────────────────────────────────────
  80     Apache — Web application
  3306   MySQL  — Database
  5000   Station Flask — local video/API
  5001   Admin Video Server — SocketIO relay
  8554   RTSP (mediamtx) — video stream
  55200  Raw Camera TCP — station → admin

================================================================================
  TROUBLESHOOTING
================================================================================

  "Admin server unreachable"  → Check Tailscale is running on both PCs.
  "Camera not found"          → Change CAMERA_INDEX in site_config.json.
  "Model not found"           → Ensure best_openvino_model\ is present.
  "RTSP disabled"             → Place mediamtx.exe + ffmpeg.exe next to .exe
  "DB connection failed"      → Check Laragon MySQL is running; verify config.php.
  "Site disabled by Admin"    → Contact admin at http://<admin-ip>/Admin/

================================================================================
