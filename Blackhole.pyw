#! python3
# -*- coding: utf-8 -*-
# ┌─────────────────────────────────────────────────────┐
# │ Blackhole 0.1 - A fiddler replacement in python     │
# ├─────────────────────────────────────────────────────┤
# │ Copyright (c) 2012 Amadeusguo                       │
# │ http://amadeus.herokuapp.com/                       │
# │ Licensed under the MIT license.                     │
# └─────────────────────────────────────────────────────┘

import os
import sys
import logging
# rotateLogger = RotatingFileHandler('data/log/log.txt', maxBytes=100*1024*1024, backupCount=3)
# logging.basicConfig(level = logging.DEBUG, handlers=(rotateLogger,))
logging.basicConfig(level = logging.DEBUG)

# on mac, __file__ return the file name only
cwd = os.path.dirname(__file__) or '.'
os.chdir(cwd)

if len(sys.argv) > 1:
    CONFIG_FILE = sys.argv[1]
else:
    CONFIG_FILE = 'config.ini'
    sys.argv.append(CONFIG_FILE)

sys.path.insert(0, 'lib')

__version__ = '0.2'

from blackhole.confparser import getConfig
import blackhole.router as router
import blackhole.ui.tk_ui as ui


if __name__=='__main__':

    config = getConfig(CONFIG_FILE)
    config.version = __version__
    config.config_file = CONFIG_FILE

    router.run(config)
    ui.init(config)
