import sys
import faulthandler
faulthandler.enable(all_threads=True)

from someui import Window

root = Window()

root.mainloop()