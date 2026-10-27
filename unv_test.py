import asyncio
from pathlib import Path

import skia

import someui
from someui import PlacingConfig, MyPlacingHint
from someui.threadsafe import async_ui_thread, widget

IMG_DIR = Path(r'C:\Users\zcveo\Desktop\UUI-2\sc_cache')

async def loop(recall, dec):
    c = 0
    lbl: someui.Label = widget(tick)
    while True:
        c += 1#
        lbl.set_text(f'Second: {c}')
        await asyncio.sleep(1)


class Image(someui.Label):
    def __init__(self, parent, fp=None):
        super().__init__(parent)
        if fp:
            self._image = skia.Image.open(fp)
        else:
            self.set_text('No image')
            self._image = None
        self._exc = None

    def set_image(self, fp):
        try:
            self._image = skia.Image.open(f'{fp}')
        except Exception as _ex:
            self.set_text(f'{_ex.__class__.__name__}: {_ex}')
            self._image = None

    def draw_self(self, ctx: skia.Canvas):
        if self._image:
            ctx.drawImageRect(self._image, skia.Rect(0, 0, self.width, self.height))
        else:
            super().draw_self(ctx)


root = someui.GLFWWindow(width=1000)
#Cursor(root)

right_panel = someui.Container(root, '#888')
right_panel.place(PlacingConfig(relative_x=0.75, relative_width=0.25, relative_height=1))

main_panel = someui.Container(root)
main_panel.place(PlacingConfig(relative_width=0.75, relative_height=1))

img = Image(main_panel)
img.rel_place(rel_width=1, rel_height=1)

settings_panel = someui.Container(root, '#888c', blur_sigma=12)

def close_settings():
    settings_panel.enabled = False

title = someui.Label(settings_panel, 'Settings', font_size=20)
title.set_align('center', 'center')
title.place(someui.PlacingConfig(relative_width=1.0))
close = someui.Button(settings_panel, 'X', close_settings)
close.set_size(*close.get_size_hint())
close.rel_place(rel_x=1, rel_y=0, x_offset=str(int(-close.width)))

settings_panel.z = right_panel.z + 2
settings_panel.enabled = False
settings_panel.place(PlacingConfig(relative_x=0.20, relative_width=0.6, relative_y=0.05, relative_height=0.9))
settings_panel.scroll_enabled = False

tick = someui.Label(settings_panel, 'No text')
tick.place()

def open_settings():
    settings_panel.enabled = True

settings_btn = someui.Button(right_panel, 'Settings', open_settings)
settings_btn.place(PlacingConfig(relative_width=1))

def create_select_callback(path):
    return lambda: img.set_image(path)

img_selector = someui.Container(settings_panel, bg='#ffff0000')
img_selector.name = 'ImgSelector'
img_selector.mcfg.propagate = True
img_selector.place(y='auto')

imgs = []

for root_path, folders, files in IMG_DIR.walk():
    for i in files:
        i = root_path / i
        ext = i.name.split('.')[-1]
        if ext not in ['png', 'jpg', 'jpeg']:
            continue
        btn = someui.Button(img_selector, f'{i}'.replace(f'{IMG_DIR}', ''), create_select_callback(i))
        btn.place(y='auto')

dp = async_ui_thread(loop)

root.mainloop()