import sys
import os
import subprocess
import platform

# Configuration
APP_NAME = "cooking"
MAIN_FILE = "main.py"
ICON_WIN = os.path.join("assets", "app-win.ico")
ICON_MAC = os.path.join("assets", "app-mac.icns")


def build():
    cmd = [
        "uv", "run", "pyinstaller",
        "--onefile",
        "--clean",
        "--name", APP_NAME,
    ]

    system_os = sys.platform
    icon_arg = None

    print(f"--- Detected System: {platform.system()} ({system_os}) ---")

    # Windows Logic
    if system_os.startswith('win'):
        if os.path.exists(ICON_WIN):
            icon_arg = ICON_WIN
            print(f"[+] Using Windows Icon: {ICON_WIN}")
        else:
            print(f"[!] Warning: {ICON_WIN} not found. Building with default icon.")

    # macOS Logic
    elif system_os.startswith('darwin'):
        if os.path.exists(ICON_MAC):
            icon_arg = ICON_MAC
            print(f"[+] Using macOS Icon: {ICON_MAC}")
        else:
            print(f"[!] Warning: {ICON_MAC} not found. Building with default icon.")

    # Linux Logic
    else:
        print("[i] Linux detected. Skipping icon embedding.")

    if icon_arg:
        cmd.append(f"--icon={icon_arg}")

    cmd.append(MAIN_FILE)

    print(f"\nExecuting command:\n{' '.join(cmd)}\n")

    try:
        subprocess.check_call(cmd)
        print("\n[SUCCESS] Build finished! Check the 'dist' folder.")
    except subprocess.CalledProcessError:
        print("\n[ERROR] Build failed.")
        sys.exit(1)


if __name__ == "__main__":
    build()