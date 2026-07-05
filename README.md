**  HARDWARE REQUIREMENTS (Station PC)
======================================================**

  The station detection system requires the following hardware:

  Component               Purpose
  ──────────────────────────────────────────────────────────────────────────────
  Arduino Uno R3          Microcontroller — reads weight and sends via serial
  HX711 Load Cell Amp.    Amplifier module — bridges load cell sensor to Arduino
  Load Cell (any range)   Measures item weight placed on the platform
  USB Webcam (laptop camera or else)  Camera feed for AI object detection
  USB Cable (Type-B)      Arduino → Station PC connection

  Wiring (HX711 → Arduino Uno R3):
  ─────────────────────────────────
    HX711 VCC  →  Arduino 5V
    HX711 GND  →  Arduino GND
    HX711 DT   →  Arduino Pin 3  (Data)
    HX711 SCK  →  Arduino Pin 2  (Clock)

  Arduino Sketch:
  ───────────────
  Flash the Arduino with a sketch that reads from the HX711 and sends weight
  values as plain text over Serial at 9600 baud, one reading per line.
  Example output format:  0.45   (weight in kg or g, one decimal)

  The system auto-detects the Arduino on these COM ports (in order):
    COM7 → COM11 → COM8 → COM6 → COM3
  If your Arduino appears on a different port, update the list in main_system.py
  at line 822:  for port in ("COM7", "COM11", "COM8", "COM6", "COM3"):

  Weight Thresholds (adjustable in main_system.py):
  ──────────────────────────────────────────────────
    START_THRESHOLD = 0.4   ← item placed (kg) — starts detection session
    END_THRESHOLD   = 0.35  ← item removed    — ends detection session

  NOTE: The system runs WITHOUT the Arduino (weight sensor) but detection will
        not trigger automatically — it will only show the camera feed.

**code for arduino uno r3 to flash:**


#include "HX711.h"

#define DOUT 2
#define CLK  3

HX711 scale;

// Invert calibration factor to fix negative readings
float calibration_factor = -179.40;

void setup() {
  Serial.begin(9600);

  scale.begin(DOUT, CLK);
  scale.set_scale(calibration_factor);
  scale.tare();              // Zero the scale

  Serial.println("Scale ready.");
}

void loop() {
  if (!scale.is_ready()) {
    delay(50);
    return;
  }

  // Get stable averaged reading
  float weight = scale.get_units(10);

  // Output PURE number only
  Serial.println(weight, 2);

  delay(50);
}


**================================================================================
  TOOLS & VERSIONS
================================================================================**

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

**================================================================================
  PROJECT STRUCTURE
================================================================================
**
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

**================================================================================
  CLONING FROM GITHUB
================================================================================**

  Repository: https://github.com/TeeChinYean/Degree_Final_Year_Project.git

  After cloning, the following files are NOT included in the repo and must be
  obtained separately before the project will work:

  ┌──────────────────────────────────────┬──────────┬────────────────────────────────────────────────────┐
  │  File / Folder                       │  Size    │  How to Get                                        │
  ├──────────────────────────────────────┼──────────┼────────────────────────────────────────────────────┤
  │  station/main_system/ffmpeg.exe      │  ~97 MB  │  https://www.gyan.dev/ffmpeg/builds/               │
  │  station/main_system/mediamtx.exe   │  ~51 MB  │  https://github.com/bluenviron/mediamtx/releases   │
  │  station/main_system/main_system.exe│  ~8 MB   │  Build with PyInstaller (see SETUP STEPS > Part C) │
  │  station/setup.exe                  │  ~11 MB  │  Build with PyInstaller (see SETUP STEPS > Part C) │
  │  venv/                              │  Large   │  Run: pip install -r requirements.txt               │
  └──────────────────────────────────────┴──────────┴────────────────────────────────────────────────────┘

  Files that ARE included in the repo (available after clone):
  ✅ All PHP source files  (Front-end/, Admin/)
  ✅ Python source files   (main_system.py, admin_video_server.py, setup.py)
  ✅ AI model files        (best_openvino_model/best.xml, best.bin)
  ✅ website.sql           (database schema + seed data)
  ✅ requirements.txt      (Python dependencies list)
  ✅ README.txt

  Quick start after cloning:
  1. git clone https://github.com/TeeChinYean/Degree_Final_Year_Project.git
  2. Copy cloned folder into  F:\laragon\www\
  3. Download ffmpeg.exe and mediamtx.exe (links above) → place in station\main_system\
  4. python -m venv venv  →  venv\Scripts\activate  →  pip install -r requirements.txt
  5. Follow SETUP STEPS A, B, C below.

**================================================================================
  SETUP STEPS
================================================================================**

  ── A. Web Application (Laragon) ─────────────────────────────────────────────

  1. Install Laragon and start Apache + MySQL.
  2. Place project files in:  F:\laragon\www\
  3. Open Laragon → Database, create a database named  website
  4. Import the database schema:
       a. Download  website.sql  from the GitHub repository.
       b. Open HeidiSQL (comes with Laragon) or phpMyAdmin.
       c. Select the  website  database.
       d. Go to  File → Load SQL file  (HeidiSQL)
               or  Import → Choose File  (phpMyAdmin)
       e. Select  website.sql  and click  Execute / Go.
     ─ OR ─ via command line:
       mysql -u root -p website < website.sql
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

**================================================================================
  PORTS USED
================================================================================**

  Port   Service
  ─────────────────────────────────────────────
  80     Apache — Web application
  3306   MySQL  — Database
  5000   Station Flask — local video/API
  5001   Admin Video Server — SocketIO relay
  8554   RTSP (mediamtx) — video stream
  55200  Raw Camera TCP — station → admin

**================================================================================
  TROUBLESHOOTING
================================================================================**

  "Admin server unreachable"  → Check Tailscale is running on both PCs.
  "Camera not found"          → Change CAMERA_INDEX in site_config.json.
  "Model not found"           → Ensure best_openvino_model\ is present.
  "RTSP disabled"             → Place mediamtx.exe + ffmpeg.exe next to .exe
  "DB connection failed"      → Check Laragon MySQL is running; verify config.php.
  "Site disabled by Admin"    → Contact admin at http://<admin-ip>/Admin/

================================================================================
