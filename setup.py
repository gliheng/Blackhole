import os
import sys

from cx_Freeze import setup, Executable

name = 'Blackhole'
icon = 'data/img/blackhole.ico'
upgrade_code = '{86a85bac-52ff-4018-0e94-3afcc9e1ad0d}'

base = None
exe_name = name
if sys.platform == 'win32':
    base = 'Win32GUI'
    exe_name += '.exe',

build_exe_options = {
    'includes': ['tkinter'],
    'include_files': ['config.ini', 'data', 'example'],
    'bin_path_excludes': [r'C:\Program Files (x86)\git\bin'],
    'packages': ['blackhole', 'wsgiserver', 'tkinter'],
    'path': ['lib'] + sys.path,
    'icon': icon
}

bdist_msi_options = {
    'upgrade_code': upgrade_code,
#    'data': {
#        'Registry': [
#        ]
#    }
}

bdist_mac_options = {
    'iconfile': icon
}

setup(
    name = name,
    version = '0.3',
    description = 'Elite web proxy debugger',
    options = {
        'build_exe' : build_exe_options,
        'build_msi' : bdist_msi_options,
        'build_mac' : bdist_mac_options
    },
    executables = [Executable(
        'Blackhole.pyw',
        base=base,
        targetName=exe_name,
        shortcutName='Blackhole',
        shortcutDir='DesktopFolder'
    )]
)
