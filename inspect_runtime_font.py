import tkinter as tk
from tkinter import font as tkfont
import main

app = main.TrendCenterApp()
app.withdraw()
print('APP_FONT_FAMILY=', main.APP_FONT_FAMILY)
print('APP_FONT_FILE=', main.APP_FONT_FILE)
print('FONT_BOLD=', main.FONT_BOLD)
for _named in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont', 'TkHeadingFont'):
    print(_named, '=', tkfont.nametofont(_named).actual())
probe = tk.Label(app, text='اختبار Cocon')
probe.pack()
app.update_idletasks()
print('LABEL_FONT=', probe.cget('font'))
app.destroy()
