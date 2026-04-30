"""Build script: pyinstaller --onefile main.py --name TinyPNGCompressor"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

CMD = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    "--name", "TinyPNGCompressor",
    "--hidden-import", "tinify",
    "--hidden-import", "DrissionPage",
    "--hidden-import", "PIL.PngImagePlugin",
    "--hidden-import", "PIL.JpegImagePlugin",
    "--clean",
    str(ROOT / "main.py"),
]

print(f"Running: {' '.join(CMD)}")
subprocess.run(CMD, cwd=str(ROOT), check=True)
print("\nBuild complete: dist/TinyPNGCompressor.exe")
