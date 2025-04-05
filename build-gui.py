import PyInstaller.__main__
import os
import shutil

if os.path.exists("./pdav.py") == True:
    os.remove("./pdav.py")
if os.path.exists("./pdav") == True and os.path.exists("./pdav.py") == False:
    shutil.copy2("./pdav", "./pdav.py")

PyInstaller.__main__.run([
    "--name=pdav-gui",
    "--clean",
    "--onefile",
    "--windowed",
    "pdav-gui.py"
])