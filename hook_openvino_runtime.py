"""
Runtime hook: tell OpenVINO where its plugin DLLs are inside the bundle.
This runs before main_system.py imports openvino.
"""
import os
import sys

if getattr(sys, 'frozen', False):
    # When frozen, _MEIPASS points to _internal/
    bundle_dir = sys._MEIPASS
    ov_libs = os.path.join(bundle_dir, 'openvino', 'libs')
    
    # Add to PATH so Windows can find the DLLs
    os.environ['PATH'] = ov_libs + os.pathsep + os.environ.get('PATH', '')
    
    # OpenVINO uses this env var to locate plugins
    os.environ['OV_PLUGINS_DIR'] = ov_libs
    
    # Also add DLL directory (Python 3.8+)
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(ov_libs)
