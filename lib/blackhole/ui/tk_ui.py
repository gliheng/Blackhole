import re
import sys
import subprocess
import threading 

import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger(__name__)

from tkinter import *
from tkinter.ttk import *

import qrcode

from PIL import Image, ImageTk

from blackhole.reghandler import RegHandler
import blackhole.router as server
from blackhole.confparser import getConfig
from blackhole.utils import get_res

from ..external import tunnel


class MainFrame(Frame):

    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.pack(expand=YES, fill=BOTH, padx=4, pady=4)

        self.createUI()
        self.captureActve = False
        # self.centerWindowOnScreen()

        # self.capture_btn.invoke()
    
    def quit(self):
        sys.exit(0)
        
    def createUI(self):

        note = Notebook(self)

        tab1 = Frame(note)
        tab2 = Frame(note)

        note.add(tab1, text = "Essential", compound=TOP)
        note.add(tab2, text = "Utility", compound=TOP)
        note.pack(expand=YES, fill=BOTH)

        self.setupTab1(tab1)
        self.setupTab2(tab2)

        # status bar
        self.status_bar = Label(self, text=INITMSG, style='Status.TLabel')
        self.status_bar.pack(side=BOTTOM, expand=NO, fill=X)

        # size is not controlled by children
        self.pack_propagate(0)

        if sys.platform == 'win32':
            self.config(width=190, height=310)
        else:
            self.config(width=250, height=360)

    def layoutTab(self, tab):
        tab.rowconfigure(0, weight=1, minsize=80)
        tab.rowconfigure(1, weight=1, minsize=80)
        tab.rowconfigure(2, weight=1, minsize=80)
        tab.columnconfigure(0, weight=1, minsize=80)
        tab.columnconfigure(1, weight=1, minsize=80)

    def setupTab1(self, tab):

        btn = Button(tab, text='Capture', command=self.toggleCapture)
        btn.config(image=IMAGES['link'], compound=TOP)
        btn.grid(row=0, column=0, sticky=W+E+N+S)

        self.capture_btn = btn

        btn = Button(tab, text="Tunnel", command=self.toggleTunnel)
        btn.config(image=IMAGES['tunnel'], compound=TOP)
        btn.grid(row=0, column=1, sticky=W+E+N+S)

        self.tunnel_btn = btn

        btn = Button(tab, text="Config", command=ConfigWin.toggle)
        btn.config(image=IMAGES['config'], compound=TOP)
        btn.grid(row=1, column=0, sticky=W+E+N+S)

        btn = Button(tab, text="Log", command=LogWin.toggle)
        btn.config(image=IMAGES['log'], compound=TOP)
        btn.grid(row=1, column=1, sticky=W+E+N+S)

        btn = Button(tab, text="Quit", command=self.quit)
        btn.config(image=IMAGES['quit'], compound=TOP)
        btn.grid(row=2, column=0, sticky=W+E+N+S)
        self.layoutTab(tab)

    def setupTab2(self, tab):
        # tab2
        btn = Button(tab, text="ClearCache", command=self.clearCache)
        btn.config(image=IMAGES['clearCache'], compound=TOP)
        btn.grid(row=0, column=0, sticky=W+E+N+S)

        btn = Button(tab, text="ClearCookie", command=self.clearCookie)
        btn.config(image=IMAGES['clearCookie'], compound=TOP)
        btn.grid(row=0, column=1, sticky=W+E+N+S)

        btn = Button(tab, text="Qrcode", command=self.qrcode)
        btn.config(image=IMAGES['qrcode'], compound=TOP)
        btn.grid(row=1, column=0, sticky=W+E+N+S)

        self.layoutTab(tab)

    def centerWindowOnScreen(self):
        win = self.winfo_toplevel()
        win.update_idletasks()

        width = win.winfo_width()
        height = win.winfo_height()
        xoffset = (win.winfo_screenwidth()-width)/2
        yoffset = (win.winfo_screenheight()-height)/2-100
        win.geometry("%dx%d%+d%+d" % (width, height, xoffset, yoffset))

    def toggleCapture(self):
        ''' Capture button toggle handler
        '''

        if self.captureActve:
            RegHandler.deactivate()
            self.captureActve = False

            self.capture_btn.config(text='Capture', image=IMAGES['link'])
            self.status_bar.config(text='Server has stopped')

        else:
            def activate(service=None):
                # set registry on windows
                try:
                    RegHandler.activate(config.port, service)
                except:
                    pass
                else:
                    self.captureActve = True

                    self.capture_btn.config(text='Stop', image=IMAGES['unlink'])
                    self.status_bar.config(text=RUNMSG)

            if sys.platform == 'darwin':
                NetworkSelector.toggle(activate)
            else:
                activate()

    def toggleTunnel(self):
        ''' Capture button toggle handler
        '''
        TunnelPanel.toggle()


    def clearCache(self):
        ''' clearCache
        '''
        # This does not work well
        # subprocess.Popen('rundll32.exe InetCpl.cpl,ClearMyTracksByProcess 8')
        cmd = get_res('data/bin/CleanIETempFiles.exe') + ' -t -q'
        logger.info('Starting proc: %s' % cmd)

        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            startupinfo = None

        subprocess.Popen(cmd, startupinfo=startupinfo)

    def clearCookie(self):
        ''' clearCookie
        '''
        cmd = 'rundll32.exe InetCpl.cpl,ClearMyTracksByProcess 2'
        logger.info('Starting proc: %s' % cmd)

        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        else:
            startupinfo = None
        subprocess.Popen(cmd, startupinfo=startupinfo)

    def qrcode(self):
        QRCodePanel.toggle()


class ToolWindow(Toplevel):
    ''' A singleton window class
    '''

    def __init__(self, parent, preserveState=False):
        self.preserveState = preserveState
        Toplevel.__init__(self, parent)
        # self.attributes('-toolwindow', True)
        self.transient(parent)
        self.focus()
        # self.lift()

        self.protocol("WM_DELETE_WINDOW", self.__toggle)
        self.bind('<Escape>', lambda e: self.__toggle())

    def __toggle(self):
        if self.preserveState:
            if self.state() == 'withdrawn':
                self.deiconify()
            else:
                self.withdraw()

        else:
            self.destroy()

            cls = self.__class__
            delattr(cls, 'inst')

    @classmethod
    def getInstance(cls):
        if hasattr(cls, 'inst'):
            return cls.inst

    @classmethod
    def toggle(cls, *args):
        ''' Toggle log window visibility
        '''
        if not hasattr(cls, 'inst'):
            cls.inst = cls(root, *args)
        else:
            cls.inst.__toggle()


class NetworkSelector(ToolWindow):

    def __init__(self, parent, callback):
        ToolWindow.__init__(self, parent)
        self.callback = callback

        services = subprocess.check_output('networksetup -listallnetworkservices', shell=True)
        services = services.splitlines()[1:]

        self.serviceVar = StringVar()
        for service in services:
            Radiobutton(self, text=service, variable=self.serviceVar, value=service, command=self.onSelect).pack(side=TOP, anchor=W)

    def onSelect(self):
        selected = self.serviceVar.get()

        if hasattr(self, 'callback'):
            self.callback(selected)

        self.destroy()


class QRCodePanel(ToolWindow):
    '''
    window that generate qrcode on input
    '''
    def __init__(self, parent):
        ToolWindow.__init__(self, parent)
        self.geometry('400x400')

        self.label = None

        self.entry = entry = Entry(self, width=30)
        entry.pack(padx=6, pady=6)
        entry.bind('<KeyRelease>', self.genQRCode)

    def genQRCode(self, e):
        if self.label:
            self.label.pack_forget()
            self.label.destroy()
            self.label = None

        s = self.entry.get()
        img = qrcode.make(s)

        tkimg = ImageTk.PhotoImage(img.resize((300, 300), Image.ANTIALIAS))

        self.label = Label(self, image=tkimg, anchor=CENTER)
        self.image = tkimg # keep a reference, so that it's not GCed
        self.label.pack(padx=6, pady=6, expand=YES, fill=BOTH)


class QRCodeShow(Toplevel):

    def __init__(self, parent, s, x=0, y=0):
        Toplevel.__init__(self, parent)
        self.overrideredirect(True)
        self.lift()
        self.transient(parent)

        img = qrcode.make(s)

        tkimg = ImageTk.PhotoImage(img.resize((300, 300), Image.ANTIALIAS))

        self.label = Label(self, image=tkimg, anchor=CENTER)
        self.image = tkimg # keep a reference, so that it's not GCed
        self.label.pack(padx=6, pady=6, expand=YES, fill=BOTH)

        self.setPosition(x, y)

    def setPosition(self, x, y):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
    @classmethod
    def show(cls, parent, s, x, y):
        if not hasattr(cls, 'inst'):
            cls.inst = QRCodeShow(parent, s, x, y)

    @classmethod
    def hide(cls):
        if hasattr(cls, 'inst'):
            cls.inst.destroy()
            del cls.inst


class TunnelPanel(ToolWindow):

    tunnel = None

    IDLE = 0
    CONNECTING = 1
    CONNECTED = 2

    def __init__(self, parent):
        ToolWindow.__init__(self, parent, True)
        self.geometry('200x200')

        self.btn = Button(self, text='Connect', command=self.onConnect)
        self.btn.pack(padx=6, pady=6)
        self.labelFrame = Frame(self)
        self.labelFrame.pack()

        self.__state = self.IDLE
        self.__changed = False
        self.activeHosts = set()
        self.timer = self.master.after(1000, self.refresh)

    def run(self):
        hosts = [tunnel['remote'] for tunnel in config.tunnels]
        self.tunnel = tunnel.Tunnel(config.port, hosts, config.tunnelServer)
        self.tunnel.onMsg += self.onMsg

        self.tunnel.start()

    def onMsg(self, signal, text):
        # this method is run in another thread
        # manipulating the UI is prohibited, since Tkinter is not thread safe
        if signal == 'connect':
            self.activeHosts.add(text)
            self.__state = self.CONNECTED
            self.__changed = True

        elif signal == 'disconnect':
            self.activeHosts.remove(text)

            if not self.activeHosts:
                self.__state = self.IDLE

            self.__changed = True

    def refresh(self):
        self.refreshUI()
        self.timer = self.master.after(1000, self.refresh)

    def clearLabel(self):
        for label in self.labelFrame.winfo_children():
            label.pack_forget()
            label.destroy()

    def refreshUI(self):
        if not self.__changed:
            return

        self.clearLabel()

        if self.__state == self.CONNECTING:
            self.btn.config(text='Connect')
            label = Label(self.labelFrame, text='Connecting...')
            label.pack()

        elif self.__state == self.CONNECTED:
            self.btn.config(text='Disconnect')

            match = {tunnel['remote']: tunnel['local'] for tunnel in config.tunnels if tunnel['remote'] in self.activeHosts}

            for host, domain in match.items():
                s = host + '\n---> ' + domain
                # add label
                label = Label(self.labelFrame, text=s, justify=CENTER)

                label.bind('<Enter>', lambda e, host=host: self.showQRCode(e, host))
                label.bind('<Leave>', lambda e: QRCodeShow.hide())
                label.pack()

        elif self.__state == self.IDLE:
            self.btn.config(text='Connect')

        self.__changed = False

    def showQRCode(self, e, host):
        widget = e.widget
        x = widget.winfo_rootx() + 15 + widget.winfo_width()
        y = widget.winfo_rooty() - 100
        QRCodeShow.show(self, host, x, y)

    def onConnect(self):
        if not config.tunnels:
            tkinter.messagebox.showinfo('Warning', 'At lease one tunnel should be configured to use')
            return

        if self.__state == self.CONNECTING or self.__state == self.CONNECTED:
            self.__state = self.IDLE
            self.__changed = True
            self.refreshUI()

            self.tunnel.stop()
        else:
            self.__state = self.CONNECTING
            self.__changed = True
            self.refreshUI()

            if not self.tunnel or not self.tunnel.is_alive():
                self.run()

    def destroy(self):
        self.master.after_cancel(self.timer)
        super().destroy()

class ConfigWin(ToolWindow):
    ''' This is the config window
    '''
    def __init__(self, parent):
        ToolWindow.__init__(self, parent)
        self.title('Config')

        topPanel = Frame(self)
        topPanel.pack(expand=YES, fill=BOTH)

        self.edit = Text(topPanel, undo=True)
        self.edit.configure(font='consolas 10')
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
        with open(config.config_file) as f:
            data = f.read()

        self.edit.insert(END, data)

    def writeConfig(self):
        # Text widget has an extra \n
        # The tkinter text widget guarantees that there is always a newline following the last character in the widget.

        data = self.edit.get('1.0', 'end-1c')

        with open(config.config_file, 'w') as f:
            f.write(data)

        self.tip.config(text='Settings was Saved!')
        self.after(2000, lambda: self.tip.config(text=''))

        global config
        config = getConfig(config.config_file)
        server.reload(config)


class LogGrid(Frame):

    match_config = {
        'file': 'Orange',
        'dir': 'Pink',
        'concat': 'PeachPuff',
        'ip': 'Salmon',
        'default': 'White'
        }

    def __init__(self, parent):
        Frame.__init__(self, parent)

        self.listgrid = Treeview(self, columns=('Status', 'URL', 'Action'), show='headings')
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

def init(_config):

    global config
    config = _config

    global INITMSG
    global RUNMSG
    global STOPMSG
    global IMAGES
    global root

    INITMSG = "Ready"
    RUNMSG = 'Capturing traffic via localhost:%d' % config.port
    STOPMSG = 'Capturing has stopped'

    root = Tk()

    IMAGES = {
        'link': PhotoImage(file=get_res('data/img/link.gif')),
        'unlink': PhotoImage(file=get_res('data/img/unlink.gif')),
        'clearCookie': PhotoImage(file=get_res('data/img/clearCookie.gif')),
        'clearCache': PhotoImage(file=get_res('data/img/clearCache.gif')),
        'config': PhotoImage(file=get_res('data/img/config.gif')),
        'log': PhotoImage(file=get_res('data/img/log.gif')),
        'quit': PhotoImage(file=get_res('data/img/quit.gif')),
        'tunnel': PhotoImage(file=get_res('data/img/tunnel.gif')),
        'qrcode': PhotoImage(file=get_res('data/img/qrcode.gif'))
    }

    # setup styles and resources
    style = Style()
    style.configure('Tip.TLabel', foreground='red')
    style.configure('Status.TLabel', padding=2, relief=SUNKEN, font='Calibri 12 bold')
    # diable menu tearoff
    root.option_add('*tearOff', FALSE)

    # main window
    main_frame = MainFrame(root)
    root.protocol('WM_DELETE_WINDOW', main_frame.quit)

    try:
        # this throws on my mac
        root.iconbitmap(default=get_res('data/img/app.ico'))
    except:
        pass

    root.resizable(False,False)
    root.title('Blackhole %s' % config.version)
    root.mainloop()

