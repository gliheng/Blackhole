import os
import re
import urllib.request, urllib.parse, urllib.error
from urllib.response import addinfourl
import mimetypes

import logging
logger = logging.getLogger(__name__)

#################### setup urllib handlers ###################
class PassErrors(urllib.request.HTTPRedirectHandler, urllib.request.HTTPDefaultErrorHandler):
    '''Handle 3xx redirection, 4xx, 500 errors
    '''

    def http_error_default(self, req, fp, code, msg, headers):
        infourl = addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        infourl.msg = msg
        return infourl

    http_error_300 = http_error_default
    http_error_301 = http_error_default
    http_error_302 = http_error_default
    http_error_303 = http_error_default
    http_error_304 = http_error_default
    http_error_305 = http_error_default
    http_error_306 = http_error_default
    http_error_307 = http_error_default

###### show debuginfo
# import http
# http.client.HTTPConnection.debuglevel = 1

# config urllib module, so that request does not automaticly use proxy setting
http_handler = urllib.request.HTTPHandler()
proxy_handler = urllib.request.ProxyHandler({})
error_handler = PassErrors()

# ProxyHandler, UnknownHandler, HTTPHandler, HTTPDefaultErrorHandler, HTTPRedirectHandler, FTPHandler, FileHandler, HTTPErrorProcessor.

opener = urllib.request.build_opener(proxy_handler, http_handler, error_handler)
urllib.request.install_opener(opener)

class ProxyServe():
    '''Proxy a file via a proxy ip or system host file
    '''
    hop_headers = ['Connection', 'Keep-alive', 'Proxy-authenticate', 'Proxy-authorization', 'TE', 'Trailers', 'Transfer-encoding', 'Upgrade']

    @classmethod
    def serve(cls, url, ip = None, environ = {}):

        method = environ.get('REQUEST_METHOD', 'GET')

        if ip:
            urlParts = urllib.parse.urlparse(url)
            url = urlParts.scheme + '://' + ip + urlParts.path
            if urlParts.query:
                url += '?' + urlParts.query

        if method == 'POST':
            f_req = urllib.request.Request(url, environ['wsgi.input'].read())
        else:
            f_req = urllib.request.Request(url)

        f_req.timeout = 15 # set timeout to avoid zombie threads

        # setting proxy also works
        # if ip:
        #     f_req.set_proxy(ip, 'http')

        # proxy request to fiddler for debugging
        # f_req.set_proxy('127.0.0.1:8888', 'http')

        # f_req.set_proxy('web-proxy.oa.com:8080', 'http')

        # attach headers for request
        for key, value in list(environ.items()):
            if key.startswith('HTTP_'):
                key = key[5:].capitalize().replace('_', '-')
                f_req.add_header(key, value)

        ctype = environ.get('CONTENT_TYPE')
        if ctype:
            f_req.add_header('Content-Type', ctype)


        try:
            f_res = urllib.request.urlopen(f_req)
        except Exception as e:
            if hasattr(e, 'reason'):
                reason = str(e.reason).encode('utf-8')
            else:
                # otherwise use class name
                reason = e.__class__.__name__

            logger.error('Error openning url (%s): %s' % (reason, url))

            headers = []
            headers.append(['Content-Type', 'text/plain'])
            headers.append(['Content-Length', str(len(reason))])
            return ('200 OK', headers, [reason])

        # forward headers
        headers = []
        for header in f_res.info().items():
            #remove hop-by-hop headers, since wsgi can't handler them
            if header[0].capitalize() not in cls.hop_headers:
                headers.append([header[0], header[1].strip()])

        return ['%d %s' % (f_res.code, f_res.msg), headers, [f_res.read()]]


class FileServe():
    '''Serve a static file from local disk
    '''

    @classmethod
    def serve(cls, path, environ = {}):

        path = os.path.abspath(path)

        logger.info('Reading file: %s' % path)

        headers = []
        try:
            status = '200 OK'
            data = open(path, 'rb').read()
        except:
            status = '404 NOT FOUND'
            data = b''

        # TODO: make this configurable?
        if os.path.splitext(path)[1] in ['.wsp', '.tmpl']:
            # if template files are applicable
            mimetype = 'text/html'
        else:
            mimetype = mimetypes.guess_type(path)[0] or 'text/plain'
        #encoding = 'gb2312' #TODO dont hard code this
        #headers.append(['Content-Type', mimetype+';charset='+encoding])
        headers.append(['Content-Type', mimetype])
        headers.append(['Content-Length', str(len(data))])

        return [status, headers, [data]]

class SpecialServe():
    '''Ad-hoc response server
    '''
    @classmethod
    def serve(cls, url, rule, environ = {}):
        if rule.startswith('*redir:'):
            loc = rule.lstrip('*redir:')
            return ['302 Found', [('Location', loc)], []]

        elif re.match(r'\*(\d+):(\w+)', rule):
            m = re.search(r'\*(\d+):(\w+)', rule).groups()
            return ['%s %s' % m, [], []]

import configparser
class ConcatServe:

    '''Serve a local file based on qzmin config.
    If qzmin file is changed, filelist is reloaded.
    If part file is changed, min-file is regenerated.
    '''
    min_list = {} # which min_files does each config_file contain
    part_list = {} # which parts does each min_file contain

    mtime_list = {} # last modify time for each file

    @classmethod
    def update(cls, fn, mtime=None):
        ''' Update a file's modification time
        '''
        if mtime is None:
            mtime = os.path.getmtime(fn)

        cls.mtime_list[fn] = mtime

    @classmethod
    def changed(cls, fn):
        ''' Verify if a file is modifed since last update
            by checking modification time
        '''
        mtime = os.path.getmtime(fn)
        if cls.mtime_list.get(fn, '') != mtime:
            return True
        else:
            return False

    @classmethod
    def serve(cls, file_path, config_file, environ={}):

        home_dir = os.path.dirname(config_file)
        min_fname = os.path.basename(file_path)
        min_path = os.path.join(home_dir, min_fname)

        # If config file is changed, filelist is reloaded.
        config_updated = False
        if cls.changed(config_file):
            cls.load_config(config_file) # update min_list and part_list
            cls.update(config_file)
            config_updated = True

        if not min_path in cls.part_list:
            # if the min file does not contain the requested file,
            # the 1st file listed in qzmin file is used
            for path in cls.part_list:
                fname = os.path.basename(path)
                if min_fname == fname:
                    min_path = path
                    break
            else:
                # can't find the concat file in config
                return

        # consider regen concat file
        if config_updated or not os.path.exists(min_path):
            cls.gen_minfile(min_path)
        else:
            for part in cls.part_list[min_path]:
                # If part file is changed, min-file is regenerated.
                if cls.changed(part):
                    cls.gen_minfile(min_path)
                    break

        # static serve generated file
        rtn = FileServe.serve(min_path, environ)
        return rtn

    @classmethod
    def load_config(cls, config_file):
        ''' load ini file config
        '''

        # remove old config
        if config_file in cls.min_list:
            for concat in cls.min_list[config_file]:
                del cls.part_list[concat]
            del cls.min_list[config_file]

        config = configparser.ConfigParser()
        config.read(config_file)

        # add new config
        home_dir = os.path.dirname(config_file)
        src_dir = config.get('global', 'src_dir', fallback='.')
        home_dir = os.path.join(home_dir, src_dir)

        concat = config['concat']

        min_list = cls.min_list[config_file] = []

        for minfile in concat.keys():

            min_path = os.path.join(home_dir, minfile)

            min_list.append(min_path)

            part_list = cls.part_list[min_path] = []

            parts = filter(lambda a: a, concat.get(minfile).strip().splitlines())
            for part_name in parts:
                part_list.append(os.path.join(home_dir, part_name))

    @classmethod
    def gen_minfile(cls, fpath):
        ''' generate min files
        '''

        logger.info('Generating min file...' + fpath)

        fil = open(fpath, 'wb')

        for part in cls.part_list[fpath]:
            fil.write(open(part, mode='rb').read())
            fil.write(b'\n')
            cls.update(part)

        fil.close()


import json
import re

# Regular expression for comments
comment_re = re.compile(
    '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
    re.DOTALL | re.MULTILINE
)

def parse_json(filename):
    """ Parse a JSON file with comments
        First remove comments and then use the json module package
        Comments look like :
            // ...
        or
            /*
            ...
            */
    """
    with open(filename) as f:
        content = ''.join(f.readlines())

        ## Looking for comments
        match = comment_re.search(content)
        while match:
            # single line comment
            content = content[:match.start()] + content[match.end():]
            match = comment_re.search(content)

        # Return json file
        return json.loads(content)

class QZServe(ConcatServe):
    '''Serve a local file based on qzmin config.
    If qzmin file is changed, filelist is reloaded.
    If part file is changed, min-file is regenerated.
    '''
    @classmethod
    def load_config(cls, config_file):
        ''' load qzmin config
        '''

        config = parse_json(config_file)
        min_files = config.get('projects', [])
        home_dir = os.path.dirname(config_file)

        cls.min_list[config_file] = []

        for minfile in min_files:

            min_path = os.path.join(home_dir, minfile['target'])

            cls.min_list[config_file].append(min_path)

            part_list = cls.part_list[min_path] = []

            for part_name in minfile['include']:
                part_list.append(os.path.join(home_dir, part_name))



if __name__ == '__main__':
    print(QZServe.serve('http://www.test.com/js/test.min.js', 'example/qzmin/config.qzmin'))
    print(QZServe.min_list)
    print(QZServe.part_list)
    print(QZServe.mtime_list)

