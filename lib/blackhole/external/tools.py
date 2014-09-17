import sys
import subprocess
import logging

from blackhole.utils import get_res


logger = logging.getLogger(__name__)

def clear_IE_cache():
    # This does not work well
    # subprocess.Popen('rundll32.exe InetCpl.cpl,ClearMyTracksByProcess 8')
    cmd = get_res('data/bin/CleanIETempFiles.exe') + ' -t -q'
    logger.info('Starting proc: %s' % cmd)

    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        startupinfo = None

    try:
        subprocess.Popen(cmd, startupinfo=startupinfo)
    except Exception as e:
        logger.error('Popen Exception: ' + e.__class__.__name__)


def clear_IE_cookie():
    cmd = 'rundll32.exe InetCpl.cpl,ClearMyTracksByProcess 2'
    logger.info('Starting proc: %s' % cmd)

    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    else:
        startupinfo = None

    try:
        subprocess.Popen(cmd, startupinfo=startupinfo)
    except Exception as e:
        logger.error('Popen Exception: ' + e.__class__.__name__)
