import os
import platform
import subprocess
import sys

def main():
    os_name = platform.system()
    
    print("-" * 50)
    print(f"Detected Operating System: {os_name}")
    print("Launching the appropriate startup script...")
    print("-" * 50 + "\n")
    
    try:
        if os_name == "Windows":
            # Launch the Windows batch script
            subprocess.call(["cmd.exe", "/c", os.path.join("scripts", "start.bat")])
        else:
            # Launch the Unix/macOS shell script
            # Ensure it is executable first
            subprocess.call(["chmod", "+x", os.path.join("scripts", "start.sh")])
            subprocess.call(["bash", os.path.join("scripts", "start.sh")])
            
    except Exception as e:
        print(f"An error occurred while trying to launch the app: {e}")
        print("\nPlease run the scripts manually:")
        print(" - Windows: Double-click 'start.bat'")
        print(" - Mac/Linux: Run 'bash start.sh' in your terminal")
        sys.exit(1)

if __name__ == "__main__":
    main()
