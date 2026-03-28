import subprocess
import os
import sys
import ctypes

def main():
    exe_name = "批量重命名.exe"
    
    # Check current directory
    if os.path.exists(exe_name):
        subprocess.Popen([exe_name])
        return

    # Check python dir
    exe_path = os.path.join(os.path.dirname(sys.executable), exe_name)
    if os.path.exists(exe_path):
        subprocess.Popen([exe_path])
        return
        
    # Check parent dir
    exe_path = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), exe_name)
    if os.path.exists(exe_path):
        subprocess.Popen([exe_path])
        return

    ctypes.windll.user32.MessageBoxW(0, f"Could not find {exe_name}", "Error", 0)
