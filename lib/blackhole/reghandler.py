import sys
import logging
import subprocess
import atexit

from blackhole.confparser import getConfig
from blackhole.utils import get_res

if sys.platform == 'win32':

    import winreg
    class RegHandler():
        '''
        Utility to active and deactivate WinINET settings
        '''

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
                0, winreg.KEY_ALL_ACCESS)

        notifier_app = get_res('./data/bin/NotifyProxyChange.exe')

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
        def activate(cls, port, service):
            if not winreg: return

            logging.info('Registry set.')

            winreg.SetValueEx(cls.key, 'ProxyEnable', 0,
                    winreg.REG_DWORD, 1)
            winreg.SetValueEx(cls.key, 'ProxyServer', 0,
                    winreg.REG_SZ, 'http=127.0.0.1:%d' % port)

            if cls.oldAutoConfig:
                winreg.DeleteValue(cls.key, 'AutoConfigURL')

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(cls.notifier_app, startupinfo=startupinfo)

        @classmethod
        def deactivate(cls):
            if not winreg: return

            logging.info('Registry restored.')

            winreg.SetValueEx(cls.key, 'ProxyEnable', 0,
                    winreg.REG_DWORD, cls.oldProxyEnable)
            winreg.SetValueEx(cls.key, 'ProxyServer', 0,
                    winreg.REG_SZ, cls.oldProxyServer)

            if cls.oldAutoConfig:
                winreg.SetValueEx(cls.key, 'AutoConfigURL', 0,
                        winreg.REG_SZ, cls.oldAutoConfig)

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(cls.notifier_app, startupinfo=startupinfo)

elif sys.platform == 'darwin':
    class RegHandler():

        @classmethod
        def activate(cls, port, service):
            cls.service = service
            subprocess.check_call('networksetup -setwebproxy "%s" %s %s' % (service, '127.0.0.1', port),
                    shell=True)
            subprocess.check_call('networksetup -setwebproxystate "%s" on' % service,
                    shell=True)

        @classmethod
        def deactivate(cls):
            if hasattr(cls, 'service'):
                subprocess.check_call('networksetup -setwebproxystate "%s" off' % cls.service,
                    shell=True)
else:
    raise Exception('Unsupported operation system!')

atexit.register(RegHandler.deactivate)
