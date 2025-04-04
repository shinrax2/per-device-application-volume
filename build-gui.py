import PyInstaller.__main__
import os
import shutil

if os.path.exists("./pdav") and not os.path.exists("./pdav.py"):
    shutil.copy2("./pdav", "./pdav.py")

PyInstaller.__main__.run([
    "--name=pdav-gui",
    "--clean",
    "--onefile",
    "--windowed",
    "pdav-gui.py"
])