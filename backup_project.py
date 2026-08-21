import shutil
import os
import datetime

def create_backup():
    # settings
    project_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"DNA_Lab_Backup_{timestamp}"
    output_path = os.path.join(project_dir, output_filename)
    
    # folders to ignore
    ignore_patterns = shutil.ignore_patterns(
        '__pycache__', '*.pyc', '*.pyo', '*.pyd', 
        '.git', '.vscode', '.idea', 'env', 'venv', 
        'build', 'dist', '*.spec', 'installer'
    )
    
    print(f"Zipping project to: {output_filename}.zip")
    
    try:
        shutil.make_archive(output_path, 'zip', project_dir)
        print("Success! Backup created.")
        print(f"Location: {output_path}.zip")
    except Exception as e:
        print(f"Error creating backup: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    create_backup()
    # Keep window open if run via double-click
    import time
    time.sleep(2)
