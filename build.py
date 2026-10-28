import os
import sys
import glob

import PyInstaller.__main__
import customtkinter

customtkinter_path = os.path.dirname(customtkinter.__file__)

# AnacondaのLibrary/binにあるDLL（Pillowがランタイムで依存する）を収集
conda_lib_bin = os.path.join(sys.prefix, "Library", "bin")

# Pillowが依存するDLLを全て収集し --add-binary で追加
binary_args = []
dll_patterns = ["jpeg*.dll", "zlib*.dll", "tiff*.dll", "png*.dll", "lzma*.dll",
                "openjp2*.dll", "freetype*.dll", "webp*.dll", "lcms2*.dll",
                "tk*.dll", "tcl*.dll"]

for pattern in dll_patterns:
    for dll in glob.glob(os.path.join(conda_lib_bin, pattern)):
        binary_args.append(f"--add-binary={dll};.")

print(f"Found {len(binary_args)} DLL(s) to bundle:")
for a in binary_args:
    print(" ", a.replace("--add-binary=", ""))

PyInstaller.__main__.run([
    'app.py',
    '--name=eBookToPDF',
    '--noconfirm',
    '--windowed',
    '--onefile',
    f'--add-data={customtkinter_path};customtkinter/',
    '--collect-all=PIL',
    '--collect-all=pyautogui',
    '--hidden-import=PIL._imaging',
    '--hidden-import=PIL.Image',
    '--hidden-import=PIL.ImageGrab',
    *binary_args,
])
