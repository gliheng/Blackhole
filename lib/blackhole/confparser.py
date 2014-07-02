import logging
logger = logging.getLogger(__name__)

import sys
import configparser
from .ui.tk_dialog import showwarning

class Configuration():

    def __init__(self, config_file):

        try:
            config = configparser.ConfigParser({'enabled': 'True'})
            config.read(config_file)

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
        self.tunnels = {}

        tunnels = config.defaults().get('tunnels', '')
        for line in tunnels.split('\n'):
            if not line:
                continue
            pair = line.split(self.sep)
            if len(pair) == 2:
                self.tunnels[pair[0]] = pair[1]


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

def getConfig(config_file):
    return Configuration(config_file)
