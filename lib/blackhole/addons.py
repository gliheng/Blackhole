
import os
import re
import gzip
import types
import tempfile
from io import BytesIO

TEMP_DIR = os.path.join(tempfile.gettempdir(), 'blackhole')

class edit():
    ''' This addon let user edit a request before it is sent
    '''
    def __init__(self, response):
        self.response = response
        self.status = response[0]
        self.headers = response[1]

        # convert wsgi iterable response to str
        if type(self.response[2]) == bytes:
            self.body = response[2]
        else:
            self.body = b''
            for chunk in self.response[2]:
                self.body += chunk

    def pre_edit(self):
        ''' This method is called before request '''

    def post_edit(self):
        ''' This method is called after request '''

        for header in self.headers:
            if header[0] == 'Content-Encoding' and header[1] == 'gzip':
                # decompress data with gzip
                self.headers.remove(header)
                self.body = gzip.GzipFile(fileobj=BytesIO(self.body)).read()
                break

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

class test():
    def __init__(self, response):
        pass

    def pre_edit(self):
        ''' This method is called before request '''

    def post_edit(self):
        ''' This method is called after request '''


if __name__ == '__main__':
    print(edit(('200 OK', [], 'Hello!')).post_edit())
