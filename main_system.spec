# -*- mode: python ; coding: utf-8 -*-
import os, sys

# Detect venv openvino libs path
VENV_DIR = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'venv')
OV_LIBS = os.path.join(VENV_DIR, 'Lib', 'site-packages', 'openvino', 'libs')
OV_PKG  = os.path.join(VENV_DIR, 'Lib', 'site-packages', 'openvino')

a = Analysis(
    ['main_system.py'],
    pathex=[],
    binaries=[
        # Explicitly bundle ALL OpenVINO plugin DLLs and TBB runtime
        (os.path.join(OV_LIBS, '*.dll'), 'openvino/libs'),
        # Bundle RTSP server (mediamtx) and FFmpeg for RTSP push
        # Download mediamtx from: https://github.com/bluenviron/mediamtx/releases
        # Download ffmpeg from: https://www.gyan.dev/ffmpeg/builds/  (ffmpeg-release-essentials)
        # Place both .exe files in the project root before building.
        ('station/main_system/mediamtx.exe', '.'),
        ('station/main_system/ffmpeg.exe',   '.'),
    ],
    datas=[
        ('best_openvino_model', 'best_openvino_model'),
        # Bundle OpenVINO cache config so device discovery works
        (os.path.join(OV_LIBS, 'cache.json'), 'openvino/libs'),
        # Bundle the full openvino package folder (Python bindings + .pyd)
        (OV_PKG, 'openvino'),
    ],
    hiddenimports=[
        'socketio',
        'socketio.client',
        'socketio.exceptions',
        'engineio',
        'engineio.client',
        'engineio.exceptions',
        'engineio.transports',
        'openvino',
        'openvino.runtime',
        'openvino._pyopenvino',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'cv2',
        'numpy',
        'PIL',
        'PIL.Image',
        'requests',
        'uuid',
        'json',
        'multiprocessing',
        'multiprocessing.managers',
        'queue',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hook_openvino_runtime.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main_system',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,   # Disable UPX - it can corrupt OpenVINO DLLs
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,   # Disable UPX for same reason
    upx_exclude=[],
    name='main_system',
)
