import os
import sys
import glob

import PyInstaller.__main__
import customtkinter

base_dir = os.path.dirname(os.path.abspath(__file__))
app_script = os.path.join(base_dir, "app.py")
customtkinter_path = os.path.dirname(customtkinter.__file__)

# Anaconda / Miniconda の Library/bin にあるDLL（PillowやTkinterがランタイムで依存する）を収集
conda_lib_bin = os.path.join(sys.prefix, "Library", "bin")

binary_args = []
dll_patterns = [
    "jpeg*.dll",
    "zlib*.dll",
    "tiff*.dll",
    "png*.dll",
    "lzma*.dll",
    "openjp2*.dll",
    "freetype*.dll",
    "webp*.dll",
    "lcms2*.dll",
    "tk*.dll",
    "tcl*.dll",
    "ffi*.dll",
]

if os.path.isdir(conda_lib_bin):
    for pattern in dll_patterns:
        for dll in glob.glob(os.path.join(conda_lib_bin, pattern)):
            binary_args.append(f"--add-binary={dll}{os.pathsep}.")

print(f"Found {len(binary_args)} DLL(s) to bundle:")
for a in binary_args:
    print(" ", a.replace("--add-binary=", ""))

PyInstaller.__main__.run(
    [
        app_script,
        "--name=eBookToPDF",
        "--noconfirm",
        "--windowed",
        "--onefile",
        f"--add-data={customtkinter_path}{os.pathsep}customtkinter/",
        "--collect-all=PIL",
        "--collect-all=pyautogui",
        "--hidden-import=PIL._imaging",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.ImageGrab",
        "--hidden-import=PIL.ImageTk",
        "--hidden-import=PIL.PdfParser",
        "--hidden-import=PIL.PdfImagePlugin",
        *binary_args,
    ]
)
