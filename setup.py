import os
import sys

from cx_Freeze import setup, Executable

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

build_exe_options = {
    'include_files': ['config.ini', 'data', 'example'],
    'bin_path_excludes': [r'C:\Program Files (x86)\git\bin'],
    'packages': ['blackhole', 'wsgiserver'],
    'path': ['lib'] + sys.path,
    'icon': 'icon.ico'
}

bdist_msi_options = {
    'upgrade_code': '{96a85bac-52af-4018-0e94-3afcc9e1ad0c}'
}

setup(
    name = 'Blackhole',
    version = '0.2',
    description = 'Elite web proxy debugger',
    options = {
        'build_exe' : build_exe_options,
        'build_msi' : bdist_msi_options
    },
    executables = [Executable(
        'Blackhole.pyw',
        base=base,
        shortcutName='Blackhole',
        shortcutDir='DesktopFolder'
    )]
)
