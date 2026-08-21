import sys
import os
import subprocess
import shutil
from tkinter import messagebox

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # In dev, use the directory of this file (utils.py) as reference to get to src/ or root
        # utils.py is in src/, so we go up one level to find the root
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def run_uninstaller(parent_window=None):
    """Attempt to run an external uninstaller `uninstall.exe` in the install folder.
    If not found, offers a best-effort removal of the install directory.
    """
    if getattr(sys, "frozen", False):
        install_dir = os.path.dirname(sys.executable)
    else:
        install_dir = os.path.dirname(os.path.abspath(__file__))

    uninstaller = os.path.join(install_dir, "uninstall.exe")

    if os.path.exists(uninstaller):
        try:
            subprocess.Popen([uninstaller])
            if parent_window:
                messagebox.showinfo("Uninstall", "Uninstaller started. The app will now exit.")
            return True
        except Exception as e:
            if parent_window:
                messagebox.showerror("Error", f"Failed to start uninstaller: {e}")
            return False
    else:
        try:
            if messagebox.askyesno("Remove files", "No uninstaller found. Attempt to remove installation folder? This is irreversible."):
                shutil.rmtree(install_dir, ignore_errors=True)
                if parent_window:
                    messagebox.showinfo("Removed", "Installation folder removed (best-effort).")
                return True
        except Exception as e:
            if parent_window:
                messagebox.showerror("Error", f"Failed to remove files: {e}")
        return False
