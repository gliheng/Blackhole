import os
import re
import sys
import types
from urllib.request import url2pathname
from urllib.parse import urlparse, unquote, quote_from_bytes
import threading
import gzip
from io import BytesIO

import logging
logger = logging.getLogger(__name__)

import wsgiserver
from blackhole.utils import Event
from blackhole.servehub import FileServe, ProxyServe, ConcatServe, QZServe, SpecialServe
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

        local file
        local dir
        host ip: get the response from an ip
        special: special serve create the response on the fly
        qzmin: qzmin js concat rule
        DEFAULT: get response as is
        '''
        if self.__class__.ip_re.match(spec):
            spec_type = 'ip'
        elif spec.startswith('*') :
            spec_type = 'special'
        elif spec.endswith(('/', '\\')):
            spec_type = 'dir'
        elif spec.endswith(('.cfg', '.qzmin')):
            spec_type = 'concat'
        elif spec == 'DEFAULT':
            spec_type = 'default'
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
            spec = route['spec']

            logger.info('{} match detected: {}'.format(spec_type, spec))
            self.onRequest({'idx': idx, 'type': spec_type, 'url': url, 'action': spec})

            if spec_type == 'file':
                res = FileServe.serve(spec, environ = environ)

            elif spec_type == 'dir':
                path = urlparse(url).path[1:]

                # remainder is the part that is not matched
                remainder = url2pathname(urlparse(url[m.end():]).path) or 'index.html'
                # remove leading /, since os.path.join must not begin with /
                if remainder.startswith('/') or remainder.startswith('\\') :
                    remainder = remainder[1:]

                file_path = os.path.join(spec, remainder)
                res = FileServe.serve(file_path, environ = environ)

            elif spec_type == 'ip':
                res = ProxyServe.serve(url, ip = spec, environ = environ)

            elif spec_type == 'concat':
                file_name = os.path.basename(urlparse(url).path)
                file_path = os.path.join(os.path.dirname(spec), file_name)

                if spec.endswith('.cfg'):
                    res = ConcatServe.serve(file_path, spec, environ = environ)
                elif spec.endswith('.qzmin'):
                    res = QZServe.serve(file_path, spec, environ = environ)

            elif spec_type == 'special':
                res = SpecialServe.serve(url, spec, environ = environ)

            elif spec_type == 'default':
                res = ProxyServe.serve(url, environ = environ)

            # make a 404 response if no res is returned
            if not res:
                res = ['404 NOT FOUND', [], ['']]

            # call addon methods after response
            if 'addons' in route:
                res = self.postOperations(route['addons'], request = environ, response = res)

            break


        # no match was found, serve the request as is
        if not res:
            logger.info('no match detected')
            self.onRequest({'idx':idx, 'type':'default', 'url': url, 'action': ''})

            res = ProxyServe.serve(url, environ = environ)

        self.onResponse({'idx': idx, 'status': res[0]})

        start_response(res[0], res[1])
        return res[2]

    def preOperations(self, addons, request):
        ''' Pre processing before response is received
        '''
        pass
      
    def postOperations(self, addons, request, response):
        ''' Post processing when response is received
        '''
        headers = response[1]
        # iterable was changed to bytes here
        body = response[2] = b''.join(response[2])

        # decompress
        hasgzip = any(header[0] == 'Content-Encoding' and 'gzip' in header[1] for header in headers)
        if hasgzip:
            body = response[2] = gzip.GzipFile(fileobj=BytesIO(body)).read()

        # TODO: assume page is utf-8 encoding
        body = response[2] = body.decode('utf-8')

        addon_list = addons.split('|')
        for addon_line in addon_list:
            if ':' in addon_line:
                addon, arg = addon_line.split(':', maxsplit=1)
            else:
                addon = addon_line
                arg = None
            if addon in self.addons:
                logger.info('Processing addon: %s' % addon)
                # if addon return empty value, it is ignored
                klass = self.addons[addon]

                ret = klass(response).post_edit(arg)
                if ret: response = ret

        # make it iterable again
        response[2] = [response[2].encode('utf-8')]

        # fix headers
        # fix content-length
        length = 0
        for item in response[2]:
            length += len(item)

        new_headers = []
        for header in headers:
            key = header[0]
            if key == 'Content-Length':
                header[1] = str(length)
            if not key == 'Content-Encoding':
                new_headers.append(header)

        return [response[0], new_headers, response[2]]

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
