from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

def showwarning(*args):
    root = Tk()
    root.withdraw()

    messagebox.showwarning(*args, parent=root)

    root.destroy()
