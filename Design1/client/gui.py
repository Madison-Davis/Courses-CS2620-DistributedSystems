# Imports
import tkinter
from tkinter import *

# Setup MACOS:
# brew install python (updates it to 3.13.1)
# brew install python-tk

gui = Tk()
Label(gui, text='Username:').grid(row=0)
e1 = Entry(gui)
e1.grid(row=0, column=1)
gui.mainloop()


