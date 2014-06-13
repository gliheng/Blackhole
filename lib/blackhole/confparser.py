import logging
logger = logging.getLogger(__name__)

import sys
import configparser

class Configuration():

    def __init__(self, config_file):

        try:
            config = configparser.ConfigParser({'enabled': 'True'})
            config.read(config_file)

            self.localOnly = eval(config.defaults().get('localhost_only', 'True'))
            self.sep = eval('"' + config.defaults().get('seperator', '\\t') + '"')
            self.port = eval(config.defaults().get('port', '8000'))
            self.allow_remote_conn = eval(config.defaults().get('allow_remote_conn', 'False'))
            self.tunnel_host = config.defaults().get('tunnel_host', 'www.example.com')

        except:
            logger.critical("Can't parse the config file: %s." % config_file)

        self.rules = []
        for sec in config.sections():
            try:
                enabled = not config.getboolean(sec, 'disabled')
            except:
                enabled = config.getboolean(sec, 'enabled')
            if not enabled: continue

            line_rules = config.get(sec, 'rules')
            for rule in line_rules.split('\n'):
                if rule:
                    self.rules.append(rule.split(self.sep))

def getConfig(config_file):
    return Configuration(config_file)
