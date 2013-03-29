import logging
import winreg
import subprocess

from blackhole.confparser import getConfig

class RegHandler():
    '''
    Utility to active and deactivate WinINET settings
    '''

    active = False

    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
            0, winreg.KEY_ALL_ACCESS)

    try:
        oldProxyEnable = winreg.QueryValueEx(key, 'ProxyEnable')[0]
        oldProxyServer = winreg.QueryValueEx(key, 'ProxyServer')[0]
    except:
        oldProxyEnable = 0
        oldProxyServer = ''

    try:
        oldAutoConfig = winreg.QueryValueEx(key, 'AutoConfigURL')[0]
    except:
        oldAutoConfig = None

    @classmethod
    def activate(cls, port):
        if cls.active: return

        logging.info('Registry set.')
        cls.active = True

        winreg.SetValueEx(cls.key, 'ProxyEnable', 0,
                winreg.REG_DWORD, 1)
        winreg.SetValueEx(cls.key, 'ProxyServer', 0,
                winreg.REG_SZ, 'http=127.0.0.1:%d' % port)

        if cls.oldAutoConfig:
            winreg.DeleteValue(cls.key, 'AutoConfigURL')

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen('./data/bin/NotifyProxyChange.exe', startupinfo=startupinfo)

    @classmethod
    def deactivate(cls):
        if not cls.active: return

        logging.info('Registry restored.')
        cls.active = False

        winreg.SetValueEx(cls.key, 'ProxyEnable', 0,
                winreg.REG_DWORD, cls.oldProxyEnable)
        winreg.SetValueEx(cls.key, 'ProxyServer', 0,
                winreg.REG_SZ, cls.oldProxyServer)

        if cls.oldAutoConfig:
            winreg.SetValueEx(cls.key, 'AutoConfigURL', 0,
                    winreg.REG_SZ, cls.oldAutoConfig)

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen('./data/bin/NotifyProxyChange.exe', startupinfo=startupinfo)
