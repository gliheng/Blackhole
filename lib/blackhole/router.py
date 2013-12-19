import os
import re
import sys
import types
from urllib.request import url2pathname
from urllib.parse import urlparse, unquote, quote_from_bytes
import threading

import logging
logger = logging.getLogger(__name__)

import wsgiserver
from blackhole.utils import Event
from blackhole.servehub import FileServe, ProxyServe, QZServe, SpecialServe
import blackhole.addons as addons

class Router():

    ip_re = re.compile(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(\:\d+)?$')
    idx = 0 # keep request index

    def __init__(self):

        self.reset_config()
        self.onRequest = Event()
        self.onResponse = Event()

    def reset_config(self):

        self.routes = []

        self.addons = {}

    def load_config(self, config):

        self.reset_config()

        self.config = config

        for rule in config.rules:
            self.add_route(*rule)

        # add addons from addons.py
        for name in dir(addons):
            klass = getattr(addons, name)

            if not isinstance(klass, type):
                continue

            self.addons[klass.__name__] = klass

    def add_route(self, url, spec, addons=None):
        '''
        Support these mappings:

        url_reg  ---> local file
        url_reg  ---> local dir
        url_reg  ---> host ip
        url_reg  ---> special
        url_reg  ---> qzmin
        '''
        if self.__class__.ip_re.match(spec):
            spec_type = 'ip'
        elif spec.startswith('*') :
            spec_type = 'special'
        elif spec.endswith('/') or spec.endswith('\\') :
            spec_type = 'dir'
        elif spec.endswith('.qzmin'):
            spec_type = 'qzmin'
        else:
            spec_type = 'file'

        route = {'type': spec_type, 'url': url, 'spec': spec}

        if addons:
            route['addons'] = addons

        self.routes.append(route)

    def handler(self, environ, start_response):

        url = environ['REQUEST_URI'].decode('ascii', errors='ignore')
        logger.info('Incoming request: %s' % url)
        
        cls = self.__class__
        idx = cls.idx = cls.idx +1

        res = None
        for route in self.routes:
            m = re.match(route['url'], url)

            if not m: continue

            # url matched the current rule

            # if 'addons' in route:
            #     res = self.preOperations(route['addons'], environ = environ)

            # if not res:

            spec_type = route['type']
            if spec_type == 'file':
                logger.info('file match detected: %s' % route['spec'])
                self.onRequest({'idx': idx, 'type': 'file', 'url': url, 'action': route['spec']})

                res = FileServe.serve(route['spec'], environ = environ)

            elif spec_type == 'dir':
                logger.info('dir match detected: %s' % route['spec'])
                self.onRequest({'idx': idx, 'type': 'dir', 'url': url, 'action': route['spec']})

                path = urlparse(url).path[1:]

                # remainder is the part that is not matched
                remainder = url2pathname(urlparse(url[m.end():]).path) or 'index.html'
                # remove leading /, since os.path.join must not begin with /
                if remainder.startswith('/') or remainder.startswith('\\') :
                    remainder = remainder[1:]

                file_path = os.path.join(route['spec'], remainder)
                res = FileServe.serve(file_path, environ = environ)

            elif spec_type == 'ip':
                logger.info('ip match detected: %s' % route['spec'])
                self.onRequest({'idx': idx, 'type': 'ip', 'url': url, 'action': route['spec']})

                res = ProxyServe.serve(url, ip = route['spec'], environ = environ)

            elif spec_type == 'qzmin':
                logger.info('qzmin match detected: %s' % route['spec'])
                self.onRequest({'idx': idx, 'type': 'qzmin', 'url': url, 'action': route['spec']})

                file_name = os.path.basename(urlparse(url).path)
                file_path = os.path.join(os.path.dirname(route['spec']), file_name)

                res = QZServe.serve(file_path, route['spec'], environ = environ)
            elif spec_type == 'special':
                logger.info('special match detected: %s' % route['spec'])

                self.onRequest({'idx': idx, 'type': 'special', 'url': url, 'action': route['spec']})

                res = SpecialServe.serve(url, route['spec'], environ = environ)

            # call addon methods after response
            if res:
                if 'addons' in route:
                    res = self.postOperations(route['addons'], request = environ, response = res)

                break

        # no match was found
        if not res:
            logger.info('no match detected')
            self.onRequest({'idx':idx, 'type':'noop', 'url': url, 'action': ''})

            res = ProxyServe.serve(url, environ = environ)

        self.onResponse({'idx':idx, 'status':res[0]})
        start_response(res[0], res[1])
        return res[2]

    def preOperations(self, addons, request):
        ''' Pre processing before response is received
        '''
        response = None

        addon_list = addons.split('|')
        for addon in addon_list:
            if addon in self.addons:
                logger.info('Processing addon: %s' % addon)
                # if addon return empty value, it is ignored
                klass = self.addons[addon]

                result = klass(response).pre_edit()

                if result: response = result

        # fix content-length
        if response:
            length = 0
            for item in response[2]:
                length += len(item)

            headers = response[1]
            for header in headers:
                if header[0] == 'Content-Length':
                    header[1] = str(length)
                    break

        return response

    def postOperations(self, addons, request, response):
        ''' Post processing when response is received
        '''
        addon_list = addons.split('|')
        for addon in addon_list:
            if addon in self.addons:
                logger.info('Processing addon: %s' % addon)
                # if addon return empty value, it is ignored
                klass = self.addons[addon]

                result = klass(response).post_edit()

                if result: response = result

        # fix content-length
        length = 0
        for item in response[2]:
            length += len(item)

        headers = response[1]
        for header in headers:
            if header[0] == 'Content-Length':
                header[1] = str(length)
                break

        return response

app = Router()
server = None

def run(config):
    app.load_config(config)

    logger.info("Server running on port %s." % config.port)

    if config.allow_remote_conn:
        # import socket
        # socket.gethostname(),
        host = ('0.0.0.0', config.port)
    else:
        host = ('127.0.0.1', config.port)

    global server
    server = wsgiserver.CherryPyWSGIServer(
        host,
        app.handler,
        numthreads = 50)


    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()

def stop():
    logger.info('Server closed.')

    server.stop()

def reload(config):
    app.load_config(config)

    logger.info('Config reloaded.')

# restore settings upon exit
# import signal
# def signal_handler(signal, frame):
#     stop()
# 
# signal.signal(signal.SIGINT, signal_handler)
# signal.signal(signal.SIGTERM, signal_handler)
