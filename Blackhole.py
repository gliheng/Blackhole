#! python3
# -*- coding: utf-8 -*-
# ┌─────────────────────────────────────────────────────┐
# │ Blackhole 0.1 - A fiddler replacement in python     │
# ├─────────────────────────────────────────────────────┤
# │ Copyright (c) 2012 Amadeusguo                       │
# │ http://amadeus.herokuapp.com/                       │
# │ Licensed under the MIT license.                     │
# └─────────────────────────────────────────────────────┘

import os
import sys

cwd = os.path.dirname(__file__)
os.chdir(cwd)

if len(sys.argv) > 1:
    CONFIG_FILE = sys.argv[1]
else:
    CONFIG_FILE = 'config.ini'
    sys.argv.append(CONFIG_FILE)

sys.path.insert(0, 'lib')

__version__ = '0.2'

import re
import time
import subprocess
import threading 

import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
#rotateLogger = RotatingFileHandler('data/log/log.txt', maxBytes=100*1024*1024, backupCount=3)
#logging.basicConfig(level = logging.DEBUG, handlers=(rotateLogger,))
logger = logging.getLogger(__name__)

from tkinter import *
#from tkinter.tix import *
from tkinter.ttk import *

from blackhole.reghandler import RegHandler
from blackhole.confparser import getConfig
import blackhole.router as server


class MainFrame(Frame):

    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.pack(expand=YES, fill=BOTH, padx=4, pady=4)

        self.createUI()
        #self.centerWindowOnScreen()

        self.capture_btn.invoke()
        
    def createUI(self):

        btn = Button(self, text='Capture', command=self.toggleCapture)
        btn.config(image=IMAGES['link'], compound=TOP)
        btn.grid(row=0, column=0, sticky=W+E+N+S)

        self.capture_btn = btn

        btn = Button(self, text="ClearCache", command=self.clearCache)
        btn.config(image=IMAGES['clearCache'], compound=TOP)
        btn.grid(row=0, column=1, sticky=W+E+N+S)

        btn = Button(self, text="ClearCookie", command=self.clearCookie)
        btn.config(image=IMAGES['clearCookie'], compound=TOP)
        btn.grid(row=0, column=2, sticky=W+E+N+S)

        btn = Button(self, text="Config", command=ConfigWin.toggle)
        btn.config(image=IMAGES['config'], compound=TOP)
        btn.grid(row=1, column=0, sticky=W+E+N+S)

        btn = Button(self, text="Log", command=LogWin.toggle)
        btn.config(image=IMAGES['log'], compound=TOP)
        btn.grid(row=1, column=1, sticky=W+E+N+S)

        btn = Button(self, text="Quit", command=app_quit)
        btn.config(image=IMAGES['quit'], compound=TOP)
        btn.grid(row=1, column=2, sticky=W+E+N+S)

        self.status_bar = Label(self, text=INITMSG, style='Status.TLabel')
        self.status_bar.grid(row=2, column=0, columnspan=3, sticky=W+E+N+S)

        self.rowconfigure(0, weight=1, minsize=80)
        self.rowconfigure(1, weight=1, minsize=80)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

    def centerWindowOnScreen(self):
        win = self.winfo_toplevel()
        width = win.winfo_width()
        height = win.winfo_height()
        xoffset = (win.winfo_screenwidth()-width)/2
        yoffset = (win.winfo_screenheight()-height)/2-100
        win.geometry("%dx%d%+d%+d" % (width, height, xoffset, yoffset))

    def toggleCapture(self):
        ''' Toggle listen button handler
        '''
        if RegHandler.active == False:

            # set registry on windows
            RegHandler.activate(config.port)


            self.capture_btn.config(text='Stop', image=IMAGES['unlink'])
            self.status_bar.config(text=RUNMSG)

        else:
            RegHandler.deactivate()

            self.capture_btn.config(text='Capture', image=IMAGES['link'])
            self.status_bar.config(text='Server has stopped')

        subprocess.Popen('data/bin/NotifyProxyChange.exe')
            
    def clearCache(self):
        ''' clearCache
        '''
        # This does not work well
        # subprocess.Popen('rundll32.exe InetCpl.cpl,ClearMyTracksByProcess 8')
        cmd = 'data/bin/CleanIETempFiles.exe -t -q'
        logger.info('Starting proc: %s' % cmd)
        subprocess.Popen(cmd)

    def clearCookie(self):
        ''' clearCookie
        '''
        cmd = 'rundll32.exe InetCpl.cpl,ClearMyTracksByProcess 2'
        logger.info('Starting proc: %s' % cmd)
        subprocess.Popen(cmd)


class ToolWindow(Toplevel):
    ''' A singleton window class
    '''

    def __init__(self, parent):
        Toplevel.__init__(self, parent)
        self.transient(parent)
        # self.attributes('-toolwindow', True)
        # self.lift() # this doesn't seem to work with transitent window

        self.protocol("WM_DELETE_WINDOW", self.__class__.toggle)

        self.bind('<Escape>', lambda e: self.toggle())

    @classmethod
    def toggle(cls):
        ''' Toggle log window visibility
        '''
        if hasattr(cls, 'inst'):
            cls.inst.destroy()
            delattr(cls, 'inst')
        else:
            setattr(cls, 'inst', cls(root))

class ConfigWin(ToolWindow):
    ''' This is the config window
    '''
    def __init__(self, parent):
        ToolWindow.__init__(self, parent)
        self.title('Config')

        topPanel = Frame(self)
        topPanel.pack(expand=YES, fill=BOTH)

        self.edit = Text(topPanel, undo = True)
        self.edit.pack(side=LEFT, expand=YES, fill=BOTH)

        scroll = Scrollbar(topPanel, orient=VERTICAL, command=self.edit.yview)
        scroll.pack(side=RIGHT, fill=Y)
        self.edit.configure(yscrollcommand=scroll.set)


        btnPanel = Frame(self)
        btnPanel.pack(side=BOTTOM, expand=NO, fill=X, pady=6)

        Button(btnPanel, text='Cancel', command=self.toggle).pack(side=RIGHT, padx=4)
        Button(btnPanel, text='Save', command=self.writeConfig).pack(side=RIGHT, padx=4)

        self.tip = Label(btnPanel, style = 'Tip.TLabel')
        self.tip.pack(side=RIGHT, padx=4)

        # creating context menu
        self.menu = Menu(parent)
        self.check = StringVar()
        self.check.set('on')
        self.menu.add_checkbutton(label='Enable', variable=self.check, onvalue='on', offvalue='off', command=self.toggleLine)
        self.edit.bind('<Button-3>', lambda e: self.showMenu(e))

        self.readConfig()
        self.edit.focus()

    def showMenu(self, e):
        try:
            # There's a text selection
            rangestart = self.edit.index('%s linestart' % SEL_FIRST)
            rangeend = self.edit.index('%s lineend' % SEL_LAST)

        except TclError:
            # There's no text selection
            rangestart = self.edit.index('%s linestart' % CURRENT)
            rangeend = self.edit.index('%s lineend' % CURRENT)

        txt = self.edit.get(rangestart, rangeend)
        self.lastRange = (rangestart, rangeend)

        if txt.lstrip().startswith('#'):
            self.check.set('off')
        else:
            self.check.set('on')
        self.menu.post(e.x_root, e.y_root)

    def toggleLine(self):
        def commentLine(txt, comment):
            # add or remove comment from a piece of text
            if comment == 'on':
                return re.sub(r'(?m)^(\s*)#', r'\1', txt)
            elif comment == 'off':
                return re.sub(r'(?m)^(\s*)', r'#\1', txt)

        args = list(self.lastRange)
        txt = self.edit.get(args[0], args[1])
        txt = commentLine(txt, self.check.get())
        args.append(txt)
        self.edit.replace(*args)

    def selectAll(self, e):
        self.edit.tag_add(SEL, '1.0', END)

    def readConfig(self):
        with open(CONFIG_FILE) as f:
            data = f.read()

        self.edit.insert(END, data)

    def writeConfig(self):
        # Text widget has an extra \n
        # The tkinter text widget guarantees that there is always a newline following the last character in the widget.
        data = self.edit.get('1.0', 'end-1c')

        with open(CONFIG_FILE, 'w') as f:
            f.write(data)

        self.tip.config(text='Settings was Saved!')
        self.after(2000, lambda: self.tip.config(text=''))

        global config
        config = getConfig(CONFIG_FILE)
        server.reload(config)


class LogGrid(Frame):

    match_config = {
        'file': 'Orange',
        'dir': 'Pink',
        'qzmin': 'PeachPuff',
        'ip': 'Salmon',
        'noop': 'White'
        }

    def __init__(self, parent):
        Frame.__init__(self, parent)

        self.listgrid = Treeview(self, columns=('Status', 'URL', 'Action'), show = 'headings')
        self.listgrid.heading('Status', text='Status', command = self.sortColumn)
        self.listgrid.heading('URL', text='URL', command = self.sortColumn)
        self.listgrid.heading('Action', text='Action', command = self.sortColumn)
        for match_type, color in self.match_config.items():
            self.listgrid.tag_configure(match_type, background=color)

        self.listgrid.column('Status', width=50, stretch=False)
        self.listgrid.column('URL', minwidth=360, stretch=True)

        self.listgrid.pack(side=LEFT, expand=YES, fill=BOTH)

        scroll = Scrollbar(self, orient=VERTICAL, command=self.listgrid.yview)
        scroll.pack(side=RIGHT, fill=Y)
        self.listgrid.configure(yscrollcommand=scroll.set)

        self.listgrid.bind('<Control-x>', lambda e: self.flush())

        #self.balloon = Balloon(parent)
        #self.balloon.bind_widget(self.listgrid, balloonmsg='Close Window')

        # creating context menu
        self.menu = Menu(parent)
        menu_actions = (
            ('Copy Data', self.copyColumnData),
            ('New Request', lambda: ...), # TODO
        )
        for (label, action) in menu_actions:
            self.menu.add_command(label=label, command=action)

        self.listgrid.bind('<Button-3>', lambda e: self.showMenu(e))

        # stores request index
        self.reqIndex = []
        # stores which request has not returned
        self.pendingIndex = []
        # stores request and response data
        self.objectStore = {}

    def sortColumn(self):
        pass

    def showMenu(self, e):
        region = self.listgrid.identify_region(e.x, e.y)
        if region != 'cell':
            return

        row = self.listgrid.identify_row(e.y)
        col = self.listgrid.identify_column(e.x)

        data = self.listgrid.item(row, 'values')[int(col[1:])-1]
        self.lastCellData = data
        self.menu.post(e.x_root, e.y_root)

    def copyColumnData(self):

        self.clipboard_clear()
        self.clipboard_append(self.lastCellData)
        

    def addRequest(self, data):

        for rec in data:
            rec['action'] = rec['action'].replace('\\', '/');
            
            idx = rec['idx']
            self.reqIndex.append(idx)
            self.pendingIndex.append(idx)
            self.objectStore[idx] = rec

            self.listgrid.insert('', 'end',
                values=('-', rec['url'], rec['action']),
                tags=(rec['type'],))

            self.listgrid.yview(MOVETO, '1.0')
            self.update_idletasks()

        # only keep 500 entries
        max_size = 500
        cur_size = len(self.reqIndex)
        if cur_size > max_size:
            size = cur_size - max_size
            removelist = self.reqIndex[:size]
            for idx in removelist:
                try:
                    self.pendingIndex.remove(idx)
                except:
                    pass
                del self.objectStore[idx]

            self.reqIndex[:size] = []

            logs = self.listgrid.get_children()[0:size]
            self.listgrid.delete(*logs)

    def addResponse(self, data):
        for rec in data:
            for idx in self.pendingIndex:
                if rec['idx'] == idx:
                    self.objectStore[idx]['status'] = rec['status']
                    self.pendingIndex.remove(idx)

                    # treeview item index is like I00A, I009
                    # item = 'I{0:0>3X}'.format(idx+1)
                    reqIdx = self.reqIndex.index(idx)
                    item = self.listgrid.get_children()[reqIdx]
                    val = list(self.listgrid.item(item, 'values'))
                    val[0] = rec['status']
                    self.listgrid.item(item, values=val)
                    break

    def flush(self):
        self.reqIndex = []
        self.pendingIndex = []
        self.objectStore = {}

        logs = self.listgrid.get_children()
        self.listgrid.delete(*logs)


class LogWin(ToolWindow):
    ''' This is the log window
    '''

    def __init__(self, parent=None):
        ToolWindow.__init__(self, parent)
        self.title('Log')
        self.geometry('550x400')

        self.loglist = LogGrid(self)
        self.loglist.pack(expand=YES, fill=BOTH)
        self.loglist.focus()

        self.reqData = [] # request data from router
        self.resData = [] # response data from router
        server.app.onRequest += self.getRequest
        server.app.onResponse += self.getReponse
        self.timer = self.master.after(100, self.logData)

        self.lock = threading.Lock()

    def getRequest(self, data):
        ''' child threads use this to get request data from router
            and store as temporary data
        '''
        with self.lock:
            self.reqData.append(data)

    def getReponse(self, data):
        ''' child threads use this to get response data from router
            and store as temporary data
        '''
        with self.lock:
            self.resData.append(data)

    def logData(self):

        with self.lock:
            if len(self.reqData)>0:
                self.loglist.addRequest(self.reqData)
                self.reqData.clear()

            if len(self.resData)>0:
                self.loglist.addResponse(self.resData)
                self.resData.clear()

        self.timer = self.master.after(100, self.logData)

    def destroy(self):
        server.app.onRequest -= self.getRequest
        server.app.onResponse -= self.getReponse
        self.master.after_cancel(self.timer)
        super().destroy()


if __name__=='__main__':

    config = getConfig(CONFIG_FILE)

    INITMSG = "Startings..."
    RUNMSG = 'Capturing traffic via localhost:%d' % config.port
    STOPMSG = 'Capturing has stopped'

    server.run(config)

    root = Tk()

    # setup styles and resources
    style = Style()
    style.configure('Tip.TLabel', foreground='red')
    style.configure('Status.TLabel', padding=2, relief=SUNKEN, font='Calibri 12 bold')
    root.option_add('*tearOff', FALSE)

    IMAGES = {
        'link': PhotoImage(file='data/img/link.gif'),
        'unlink': PhotoImage(file='data/img/unlink.gif'),
        'clearCookie': PhotoImage(file='data/img/clearCookie.gif'),
        'clearCache': PhotoImage(file='data/img/clearCache.gif'),
        'config': PhotoImage(file='data/img/config.gif'),
        'log': PhotoImage(file='data/img/log.gif'),
        'quit': PhotoImage(file='data/img/quit.gif')
    }

    def app_quit():
        ''' Quit handler
        '''
        RegHandler.deactivate()
        subprocess.Popen('data/bin/NotifyProxyChange.exe')
        # sys.exit()
        # is it ok to exit this way?
        # server.stop()
        root.quit()

    # main window
    main_frame = MainFrame(root)

    root.iconbitmap(default='data/img/app.ico')
    root.protocol('WM_DELETE_WINDOW', app_quit)
#    root.resizable(False,False)
    root.title('Blackhole %s' % __version__)
    root.mainloop()
