''' This is used before the root window is created
'''

from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox


def showwarning(*args):
    root = Tk()
    root.withdraw()

    messagebox.showwarning(*args, parent=root)

    root.destroy()
