#! python3

from tkinter import *
from tkinter.ttk import *

import urllib.request, urllib.parse, urllib.error
from urllib.response import addinfourl
from urllib.error import URLError

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

#http_handler = urllib.request.HTTPHandler()
http_handler = urllib.request.HTTPHandler(debuglevel=1)
error_handler = PassErrors()

# ProxyHandler, UnknownHandler, HTTPHandler, HTTPDefaultErrorHandler, HTTPRedirectHandler, FTPHandler, FileHandler, HTTPErrorProcessor.

opener = urllib.request.build_opener(http_handler, error_handler)
urllib.request.install_opener(opener)


class ScrolledText(Frame):
    def __init__(self, parent, height=10):
        Frame.__init__(self, parent)

        self.text = Text(self, height=height)
        self.text.pack(side=LEFT, expand=YES, fill=BOTH)

        scroll = Scrollbar(self, orient=VERTICAL, command=self.text.yview)
        scroll.pack(side=RIGHT, fill=Y)

        self.text.configure(yscrollcommand=scroll.set)
        # state = 'disabled'


class ReqPanel(Frame):
    def __init__(self, parent=None, data=None):
        Frame.__init__(self, parent)

        if data:
            self.data = data
            self.mode = 'r'
        else:
            self.data = None
            self.mode = 'w'

        self.createUI()

    def createUI(self):
        row0 = Labelframe(self, text='URL')
        row1 = Labelframe(self, text='Headers')
        row2 = Labelframe(self, text='Body')
        row3 = Frame(self)

        self.reqMethod = Combobox(row0, values=('GET', 'POST'))
        self.reqMethod.pack(side=LEFT, padx=4, pady=4)
        self.reqMethod.current(0)
        Entry(row0).pack(expand=YES, fill=X, padx=4, pady=4)

        ScrolledText(row1, height=10).pack(expand=YES, fill=BOTH, padx=4, pady=4)

        ScrolledText(row2, height=20).pack(expand=YES, fill=BOTH, padx=4, pady=4)

        Button(row3, text='Fire', command=self.fireRequest).pack(side=RIGHT)

        row0.pack(expand=YES, fill=BOTH, padx=2, pady=2)
        row1.pack(expand=YES, fill=BOTH, padx=2, pady=2)
        row2.pack(expand=YES, fill=BOTH, padx=2, pady=2)
        row3.pack(expand=YES, fill=BOTH, padx=2, pady=2)

    def fireRequest(self):
        request_method = 'GET'
        url = 'http://www.baidu.com'
        request_data  = '123'

        if request_method == 'GET':
            req = urllib.request.Request(url)
        elif request_method == 'POST':
            req = urllib.request.Request(url, data)

        #req.add_header('HOST', '')
        try:
            res = urllib.request.urlopen(req)

        except URLError as e:
            return

        print(res)

        note.add(ResPanel(), text='Response')

class ResPanel(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)

        self.createUI()

    def createUI(self):
        row0 = Labelframe(self, text='Status')
        row1 = Labelframe(self, text='Headers')
        row2 = Labelframe(self, text='Body')

        Entry(row0).pack(expand=YES, fill=X, padx=4, pady=4)

        ScrolledText(row1, height=10).pack(expand=YES, fill=BOTH, padx=4, pady=4)

        ScrolledText(row2, height=20).pack(expand=YES, fill=BOTH, padx=4, pady=4)


        row0.pack(expand=YES, fill=BOTH, padx=2, pady=2)
        row1.pack(expand=YES, fill=BOTH, padx=2, pady=2)
        row2.pack(expand=YES, fill=BOTH, padx=2, pady=2)
    

if __name__ == '__main__':
    root = Tk()
    note = Notebook(root)
    note.add(ReqPanel(), text='Request')
    note.pack(expand=YES, fill=BOTH, padx=4, pady=4)
    root.mainloop()
