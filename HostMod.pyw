#! python3
# -*- coding: utf-8 -*-
#======================================
#   Author: gliheng
#   Version: 1.0
#   Purpose: GUI for modifying the host file
#======================================

import os, sys, shelve, tempfile
from tkinter import *
import tkinter.font
from tkinter.scrolledtext import ScrolledText
#from ttk import *


ConfigFilePath = os.path.join(tempfile.gettempdir(),'HostMod.config')

def getConfig(key, default):
    try:
        cache = shelve.open(ConfigFilePath)
        settings = cache[key]
        cache.close()
    except:
        settings = default
    return settings

def saveConfig(config):
    try:
        cache = shelve.open(ConfigFilePath)
        for key, value in list(config.items()):
            cache[key] = value

        cache.close()
    except:
        raise IOError('Error saving settings')

class HostFile:

    if os.name == 'nt':
        host_path = os.path.join(os.environ.get('windir', r'C:\WINDOWS'),
            r'system32\drivers\etc\hosts')
    else:
        host_path = '/etc/hosts'

    @classmethod
    def read(cls):
        string = open(cls.host_path, 'r').read()
        return string

    @classmethod
    def write(cls, string):
        try:
            open(cls.host_path, 'w').write(string)
        except:
            import tkinter.messagebox
            tkinter.messagebox.showwarning(
                'Error',
                'Host file write error!'
            )

class InputDialog(Toplevel):
    def __init__(self, parent, title = None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        # make sure self.winfo_width get the right value
        self.update_idletasks()

        self.geometry('+%d+%d' % (parent.winfo_x()+(parent.winfo_width()-self.winfo_width())/2, parent.winfo_y()+(parent.winfo_height()-self.winfo_height())/2))

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol('WM_DELETE_WINDOW', self.cancel)

        self.initial_focus.focus_set()

        self.wait_window(self)

    #
    # construction hooks

    def body(self, master):
        Label(master, text='Label:').pack(side = LEFT)

        self.input = Entry(master)

        self.input.pack(fill = X)
        return self.input # initial focus

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = Frame(self)

        w = Button(box, text='OK', width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text='Cancel', width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.cancel)

        box.pack()

    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.result = self.input.get()
        self.cancel()

    def cancel(self, event=None):
        self.parent.focus_set()
        self.destroy()

    def validate(self):
        return 1 # override

    def apply(self):
        pass # override

class MainFrame(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self,parent)

        self.tabInd = IntVar()
        self.tabIndMax = 0
        # use list instead of dict, since list is ordered
        self.tabs = []
        self.txtCtrls = []
        self.currentTabValue = None

        # current host value
        self.currentHosts = HostFile.read()
        self.createUI(getConfig('tabs', []))
        self.setTabFromHost()

        self.pack(side=TOP, expand=YES, fill=BOTH,  padx = 4, pady = 4)

    def getState(self):
        state = {'tabs':[]}
        for tab in self.tabs:
            ind = self.tabs.index(tab)
            txtContent = self.txtCtrls[ind].get(1.0, END)[0:-1]
            if tab['value'] == self.currentTabValue:
                continue
            state['tabs'].append({'name':tab['text'],'content':txtContent})
        return state

    def createTab(self, text, content):
        ind = self.tabIndMax
        tab = Radiobutton(self.tabs_panel, text=text,
                font=NORMAL_FONT, indicatoron=NO,
                variable=self.tabInd, value=ind,
                command=lambda:self.switchTab(ind))
        self.tabIndMax += 1
        tab.pack(side=TOP, fill=X)

        txtCtrl = ScrolledText(self.txt_panel, undo = True)
        txtCtrl.insert(1.0, content)

        self.tabs.append(tab)
        self.txtCtrls.append(txtCtrl)
        return ind
            
    def switchTab(self, tabInd):
        ind = self.getIndByValue(tabInd)
        for txtCtrl in self.txtCtrls:
            txtCtrl.pack_forget()
        self.txtCtrls[ind].pack(expand=YES, fill=BOTH)

    def getIndByValue(self, value):
        for tab in self.tabs:
            if tab['value'] == value:
                return self.tabs.index(tab)
        return -1

    def removeTab(self):
        ind = self.getIndByValue(self.tabInd.get())
        if ind == -1:
            return

        tab = self.tabs.pop(ind)
        tab.pack_forget()
        tab.destroy()

        txtCtrl = self.txtCtrls.pop(ind)
        txtCtrl.pack_forget()
        txtCtrl.destroy()

        # set new current tab after removal
        if len(self.tabs) > 0:
            newInd = self.tabs[0]['value']
            self.tabInd.set(newInd)
            self.switchTab(newInd)

    def askForNewTab(self):
        dlg = InputDialog(self.master, 'New Config')
        if dlg.result:
            self.createTab(dlg.result, '')

    def createUI(self, tabs):
        self.tabs_panel = Frame(self, width=60)
        self.txt_panel = Frame(self)

        # add tab btn
        addBtn = Button(self.tabs_panel, text = '+', font=NORMAL_FONT, relief = GROOVE, command = self.askForNewTab)
        addBtn.pack(side=TOP, fill=X, pady = 4)

        # if the current hosts has no match in the tabs
        if not self.currentHosts in [tab['content'] for tab in tabs]:
            self.currentTabValue = self.createTab('Current', self.currentHosts)
        # create tabs
        for tab in tabs:
            self.createTab(tab['name'], tab['content'])

        # remove tab btn
        removeBtn = Button(self.tabs_panel, text = '-', font=NORMAL_FONT, relief = GROOVE, command = self.removeTab)
        removeBtn.pack(side=BOTTOM, fill=X)

        # bottom panel
        btnsPanel = Frame(self, height = 30)
        Button(btnsPanel, text='Quit', font=NORMAL_FONT, padx=4, pady=4, command=self.quit).pack(side=RIGHT, fill=Y)
        Button(btnsPanel, text='Save', font=NORMAL_FONT, padx=4, pady=4, command=lambda:saveConfig(self.getState())).pack(side=RIGHT, fill=Y, padx = 4)
        Button(btnsPanel, text='Set Active', font=NORMAL_FONT, padx=4, pady=4, command=self.setActiveHost).pack(side=RIGHT, fill=Y)

        self.tabs_panel.pack(side = LEFT, fill = Y, padx=2)
        self.tabs_panel.pack_propagate(NO)
        btnsPanel.pack(side = BOTTOM, fill = X)
        btnsPanel.pack_propagate(NO)
        self.txt_panel.pack(expand = YES, fill = BOTH, pady = 4)

    def setTabFromHost(self):
        '''
        get current host settings
        '''
        for tab in self.tabs:
            ind = self.tabs.index(tab)
            if self.txtCtrls[ind].get(1.0, END)[0:-1] == self.currentHosts:
                # switch to the active tab
                self.switchTab(ind)
                self.tabInd.set(ind)
                # set active tab font to bold
                tab['font'] = HIGHLIGHT_FONT
                return

    def setActiveHost(self):
        '''
        save the hosts in the current tab to the system
        '''
        ind = self.tabInd.get()
        for tab in self.tabs:
            if ind == tab['value']:
                tab['font'] = HIGHLIGHT_FONT
                hosts = self.txtCtrls[self.tabInd.get()].get(1.0, END)[0:-1]
                try:
                    HostFile.write(hosts)
                except:
                    print('Can\'t write file')
            else:
                tab['font'] = NORMAL_FONT


if __name__ == '__main__':
    root = Tk()

    width=420
    height=500
    xoffset=(root.winfo_screenwidth()-width)/2
    yoffset=(root.winfo_screenheight()-height)/2-100
    root.geometry('%dx%d%+d%+d' % (width,height,xoffset, yoffset)) 

    NORMAL_FONT = tkinter.font.Font(family='Verdana', size=10, weight='normal')
    HIGHLIGHT_FONT = tkinter.font.Font(family='Verdana', size=10, weight='bold')
    # set global font
    root.option_add('*Font', NORMAL_FONT)

    # utility function
    def selectall(event):
        event.widget.tag_add('sel','1.0','end')
    # rebind ctrl+a of text widget as 'select all'
    root.bind_class('Text','<Control-a>', selectall)

    frame = MainFrame(root)
    
    #root.resizable(False,False)
    root.title('HostMod')
    root.protocol('WM_DELETE_WINDOW', frame.quit)
    root.mainloop()
