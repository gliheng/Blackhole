import os
import re
import sys
import types
import tempfile
import subprocess
import locale
import importlib
from io import BytesIO

from blackhole.confparser import getConfig


TEMP_DIR = os.path.join(tempfile.gettempdir(), 'blackhole')

class edit():
    ''' This addon let user edit a request before it is sent
    '''
    def __init__(self, request, response):
        self.request = request
        self.response = response
        self.status = response[0]
        self.headers = response[1]
        self.body = response[2]

    def pre_edit(self):
        ''' This method is called before request '''

    def post_edit(self):
        ''' This method is called after request '''

        try:
            fd, fn = tempfile.mkstemp(prefix='tmp_', suffix='.txt', text=True, dir=TEMP_DIR)
        except OSError:
            # dir does not exist
            os.mkdir(TEMP_DIR)
            fd, fn = tempfile.mkstemp(prefix='tmp_', suffix='.txt', text=True, dir=TEMP_DIR)

        # TODO These encodings may cause bug
        fileobj = os.fdopen(fd, 'wb+')
        fileobj.write(self.body)
        fileobj.flush()
        fileobj.seek(0)

        os.system('notepad.exe %s' % fn)

        new_data = fileobj.read()
        fileobj.close()
        os.remove(fn)

        return [self.status, self.headers, new_data]

class fixcookie():
    '''
    change domain of Set-Cookie header,
    preserve leading dot
    '''

    def __init__(self, request, response):
        self.request = request
        self.response = response
        self.body = response[2]

    def post_edit(self):
        headers = self.response[1]
        if not headers or 'blackhole.orig_host' not in self.request:
            pass
        else:
            repl = r'\1' + self.request['blackhole.orig_host'] + ';'
            for header in headers:
                if header[0] == 'Set-Cookie':
                    header[1] = re.sub(r'(domain=\.?)([^;]*);', repl, header[1])

        return self.response


class weinre():

    def __init__(self, request, response):
        self.request = request
        self.response = response
        self.body = response[2]

    def post_edit(self):
        headers = self.response[1]
        
        is_html = False
        for header in headers:
            if header[0] == 'Content-Type' and header[1] == 'text/html':
                is_html = True
                break
        
        if is_html:
            html = self.body
            jsfile = self.get_config('jsfile')
            idx = html.rfind(b'</body>')
            if idx != -1:
                self.response[2] = html[:idx] + b'<script src="' + jsfile.encode() + b'"></script>' + html[idx:]
            return self.response

    def get_config(self, key):
        return getConfig().getAddonConfig('weinre', key)

class execfile():

    def __init__(self, request, response):
        self.request = request
        self.response = response
        self.body = response[2]

    def pre_edit(self, fname):
        ''' This method is called before request '''
        return self.response

    def post_edit(self, fname):
        ''' This method is called after request '''

        params = {
            'request': self.request,
            'response': self.response
        }

        try:
            s = open(fname).read()
            exec(s, params)

            # mod = importlib.__import__(fname)
            # response = mod.transform(response)

            # response[2] = response[2].decode('utf-8')
            # response[2] = response[2].encode('utf-8')
        except:
            pass

        return self.response
        # # make subprocess use utf-8 encoding for stdin
        # env = os.environ.copy()
        # env['PYTHONIOENCODING'] = 'utf-8'

        # p = subprocess.Popen([sys.executable, args],
        #         stdin=subprocess.PIPE,
        #         stdout=subprocess.PIPE,
        #         env=env)
        # codec = locale.getpreferredencoding()
        # ret, _ = p.communicate(self.body.encode('utf-8'))
        # self.response[2] = ret.decode('utf-8')
        # return self.response

class test():
    '''
    This is an addon scaffold
    '''
    def __init__(self, request, response):
        self.request = request
        self.response = response

    def pre_edit(self, args):
        ''' This method is called before request '''
        return self.response

    def post_edit(self, args):
        ''' This method is called after request '''
        return self.response



if __name__ == '__main__':
    print(edit(('200 OK', [], 'Hello!')).post_edit())
