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
import blackhole.utils as utils
from blackhole.servehub import FileServe, ProxyServe, ConcatServe, QZServe, SpecialServe
import blackhole.addons as addons


class Router():

    ip_re = re.compile(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(\:\d+)?$')

    def __init__(self):

        self.reset_config()
        self.onRequest = utils.Event()
        self.onResponse = utils.Event()
        self.idx = 0 # keep request index

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
        # use unix seprator
        spec = spec.replace('\\', '/')

        if self.__class__.ip_re.match(spec):
            spec_type = 'ip'
        elif spec.startswith('*') :
            spec_type = 'special'
        elif spec.endswith(('/')):
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

        # if request come from tunneling server client
        tunneling = False
        for tunnel in self.config.tunnels:
            if environ['HTTP_HOST'] == tunnel['remote']:
                utils.change_host(environ, tunnel['local'])
                tunneling = True
                break

        url = utils.get_absolute_url(environ)
        logger.info('Incoming request: %s' % url)
        
        # increase count
        idx = self.idx = self.idx + 1

        res = None
        match = None
        for route in self.routes:
            match = re.match(route['url'], url)

            if match:
                break

        # generate addon list
        addons = []

        if match and 'addons' in route:
            addons += route['addons'].split('|')

        if tunneling and 'addons' in tunnel:
            addons += tunnel['addons'].split('|')

        # call addon methods after request
        if addons:
            self.preOperations(addons, request=environ)

        if match:
            spec_type = route['type']
            spec = route['spec']

            logger.info('{} match detected: {}'.format(spec_type, spec))
            self.onRequest({'idx': idx, 'type': spec_type, 'url': url, 'action': spec})
        else:
            spec_type = 'default'
            spec = ''

            # no match was found, serve the request as is
            logger.info('No match detected')
            self.onRequest({'idx': idx, 'type':'default', 'url': url, 'action': ''})

        res = self.makeRequest(url, match, environ, spec_type, spec)


        # call addon methods after response
        if addons:
            self.postOperations(addons, request=environ, response=res)


        self.onResponse({'idx': idx, 'status': res[0]})

        start_response(res[0], res[1] or [])
        return res[2] or []

    def makeRequest(self, url, match, environ, spec_type, spec):

        if spec_type == 'file':
            res = FileServe.serve(spec, environ=environ)

        elif spec_type == 'dir':
            path = urlparse(url).path[1:]

            # remainder is the part that is not matched
            remainder = url2pathname(urlparse(url[match.end():]).path) or 'index.html'
            # remove leading /, since os.path.join must not begin with /
            if remainder.startswith('/') or remainder.startswith('\\') :
                remainder = remainder[1:]

            file_path = os.path.join(spec, remainder)
            res = FileServe.serve(file_path, environ=environ)

        elif spec_type == 'ip':
            res = ProxyServe.serve(url, ip = spec, environ=environ)

        elif spec_type == 'concat':
            file_name = os.path.basename(urlparse(url).path)
            file_path = os.path.join(os.path.dirname(spec), file_name)

            if spec.endswith('.cfg'):
                res = ConcatServe.serve(file_path, spec, environ=environ)
            elif spec.endswith('.qzmin'):
                res = QZServe.serve(file_path, spec, environ=environ)

        elif spec_type == 'special':
            res = SpecialServe.serve(url, spec, environ=environ)

        else:
            res = ProxyServe.serve(url, environ=environ)

        # make a 404 response if no res is returned
        if not res:
            res = ['404 NOT FOUND', [], [b'']]

        return res

    def preOperations(self, addons, request):
        ''' Pre processing before response is received
        '''
        for addon in addons:
            logger.info('Pre processing with addon: %s' % addon)

            if addon.endswith('.py'):
                klass = self.addons['execfile']
                addonObj = klass(request, None, addon)
            else:
                klass = self.addons[addon]
                addonObj = klass(request, None)

            if hasattr(addonObj, 'pre_edit'):
                addonObj.pre_edit()
      
    def postOperations(self, addons, request, response):
        ''' Post processing when response is received
        '''
        headers = response[1]
        # iterable is changed to bytes here
        body = b''.join(response[2])

        # decompress
        hasgzip = any(header[0] == 'Content-Encoding' and 'gzip' in header[1] for header in headers)
        if hasgzip:
            body = gzip.GzipFile(fileobj=BytesIO(body)).read()

        # try to get contenttype and encoding from headers
        type, coding = utils.content_type(headers)
        coding = coding or 'utf-8'

        if type == 'text/html':
            body = body.decode(coding, errors='ignore')

        response[2] = body

        for addon in addons:
            logger.info('Post processing with addon: %s' % addon)

            if addon.endswith('.py'):
                klass = self.addons['execfile']
                addonObj = klass(request, response, addon)
            else:
                klass = self.addons[addon]
                addonObj = klass(request, response)

            if hasattr(addonObj, 'post_edit'):
                addonObj.post_edit()

        if type == 'text/html':
            response[2] = response[2].encode(coding, errors='ignore')

        # body is made iterable again
        response[2] = [response[2]]

        # fix headers
        new_headers = []
        for header in headers:
            key = header[0]
            if key == 'Content-Length':
                # fix content-length
                header[1] = str(utils.get_content_length(response[2]))
            if not key == 'Content-Encoding':
                new_headers.append(header)

        response[1] = new_headers

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
