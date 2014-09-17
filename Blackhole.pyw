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
import logging.handlers

if __name__=='__main__':

    ### setup path ###
    if hasattr(sys, 'frozen'):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = os.path.abspath(os.path.dirname(__file__) or '.')
        sys.path.insert(0, os.path.join(app_dir, 'lib'))

    if len(sys.argv) > 1:
        config_file = os.path.join(os.getcwd(), sys.argv[1])
    else:
        config_file = os.path.join(app_dir, 'config.ini')
        sys.argv.append(config_file)

    config_dir = os.path.dirname(config_file)
    os.chdir(config_dir)

    import blackhole.utils as utils
    utils.register_path(app_dir, config_dir)

    ### setup logging ###
    logfile = utils.get_res('data/log/log.txt')
    try:
        os.makedirs(os.path.dirname(logfile))
    except FileExistsError:
        pass
    rotateLogger = logging.handlers.RotatingFileHandler(logfile, maxBytes=100*1024*1024, backupCount=3)
    logging.basicConfig(level=logging.DEBUG, handlers=(rotateLogger,))

    ### startup app ###
    from blackhole.confparser import getConfig
    import blackhole.router as router
    import blackhole.ui.tk_ui as ui

    config = getConfig(config_file)
    router.run(config)
    ui.init(config)
