import os
import sys

from cx_Freeze import setup, Executable

base = None
if sys.platform == "win32":
    base = "Win32GUI"

build_exe_options = {
    'include_files': ['config.ini', 'data', 'example'],
    'bin_path_excludes': [r'C:\Program Files (x86)\git\bin'],
    'packages': ['blackhole', 'wsgiserver'],
    'path': ['lib'] + sys.path,
    'icon': 'icon.ico'
}

setup(
    name = "Blackhole",
    version = "0.2",
    description = "Elite web proxy debugger",
    options = {
        "build_exe" : build_exe_options
    },
    executables = [Executable("Blackhole.pyw", base = base)]
)
