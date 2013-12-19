import os
import re
import types
import tempfile
import subprocess
from io import BytesIO

TEMP_DIR = os.path.join(tempfile.gettempdir(), 'blackhole')

class edit():
    ''' This addon let user edit a request before it is sent
    '''
    def __init__(self, response):
        self.response = response
        self.status = response[0]
        self.headers = response[1]
        self.body = response[2]

    def pre_edit(self, args):
        ''' This method is called before request '''

    def post_edit(self, args):
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

        return (self.status, self.headers, [new_data])

class transform():
    def __init__(self, response):
        self.response = response
        self.body = response[2]

    def pre_edit(self, args):
        ''' This method is called before request '''
        return self.response

    def post_edit(self, args):
        ''' This method is called after request '''
        p = subprocess.Popen(['python', args], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        ret, _ = p.communicate(self.body)
        self.response[2] = ret
        return self.response

class test():
    '''
    This is an addon scaffold
    '''
    def __init__(self, response):
        self.response = response

    def pre_edit(self, args):
        ''' This method is called before request '''
        return self.response

    def post_edit(self, args):
        ''' This method is called after request '''
        return self.response



if __name__ == '__main__':
    print(edit(('200 OK', [], 'Hello!')).post_edit())
