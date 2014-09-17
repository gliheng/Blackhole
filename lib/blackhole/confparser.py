import logging
logger = logging.getLogger(__name__)

import sys
import configparser
from .ui.tk_dialog import showwarning

__version__ = '0.3'


class Configuration():

    def __init__(self, config_file):

        try:
            self.config_file = config_file
            config = configparser.ConfigParser({'enabled': 'True'})
            config.read(config_file)
            self._config = config

            self.localOnly = eval(config.defaults().get('localhost_only', 'True'))
            self.sep = eval('"' + config.defaults().get('seperator', '\\t') + '"')
            self.port = eval(config.defaults().get('port', '8000'))
            self.allow_remote_conn = eval(config.defaults().get('allow_remote_conn', 'False'))

            self.tunnelServer = config.defaults().get('tunnel_server', '')

        except:
            logger.critical("Can't parse the config file: %s." % config_file)

        self.parseTunnels(config)
        self.parseRules(config)

    def parseTunnels(self, config):
        self.tunnels = []

        tunnels = config.defaults().get('tunnels', '')
        for line in tunnels.split('\n'):
            if not line:
                continue

            seg = line.split(self.sep)
            if len(seg) < 2:
                continue

            if len(seg) == 2:
                group = {'remote': seg[0], 'local': seg[1]}
            elif len(seg) == 3:
                group = {'remote': seg[0], 'local': seg[1], 'addons': seg[2]}

            self.tunnels.append(group)


    def parseRules(self, config):

        self.rules = []
        for sec in config.sections():
            try:
                enabled = not config.getboolean(sec, 'disabled')
            except:
                enabled = config.getboolean(sec, 'enabled')
            if not enabled: continue

            try:
                rules = config.get(sec, 'rules')
            except:
                showwarning("Error", 'Error reading configuration')
                logger.critical("Can't parse rule: %s." % sec)
                continue

            for line in rules.split('\n'):
                if not line:
                    continue
                self.rules.append(line.split(self.sep))

    def getAddonConfig(self, addon, key):
        key = addon + '.' + key
        return self._config.defaults().get(key, '')

# caching
def get_config(config_file=None):
    global _config

    if not config_file and _config:
        return _config
    else:
        _config = Configuration(config_file)
        _config.version = __version__

    return _config
