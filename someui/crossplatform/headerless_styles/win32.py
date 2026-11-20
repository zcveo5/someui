import skia
from someui import util, colors
from someui.windows.glfw_window import WindowHeaderWidgetMixin
from someui.widgets.animated_button import PrettyButton
from someui.widget import PlacingConfig, PlacementType, PlacementValue, Direction as PlacementDirection
from someui.widgets.label import Label
from someui.widget_extensions import Container
from someui.windows.platrel_window import WindowForPlatform


class HeadButton(PrettyButton):
    def __init__(self, parent, text = '', command=None, font: str | None = None, font_size: float | None = None, typeface: skia.Typeface | None = None,
                 text_color: str | None = None, background_color: str | None = None, click_color: str | None = None, hover_color: str | None = None, debug=False, font_style=None):
        super().__init__(parent, text, command, font, font_size, typeface, text_color, background_color, click_color, hover_color, debug, font_style)

    def draw_self(self, ctx: skia.Canvas):
        r = skia.Rect(0, 0, self.width, self.height)

        self._ensure_blob()
        ctx.drawRect(r, self._active_paint)
        ctx.drawTextBlob(self._blob, self._text_x_offset, self._text_y_offset, self._text_paint)


class MaximizeButton(HeadButton):
    def __init__(self, parent, text = '\uE922', command=None, font: str | None = None, font_size: float | None = None, typeface: skia.Typeface | None = None,
                 text_color: str | None = None, background_color: str | None = None, click_color: str | None = None, hover_color: str | None = None, debug=False):
        super().__init__(parent, text, command, font, font_size, typeface, text_color, background_color, click_color, hover_color, debug)
        self.window.on_maximize(self.refresh_maximize)
        self._last_sent_rect = (0, 0, 0, 0)

    def _resize(self, *_):
        new_rect = (int(self.global_x), int(self.global_y), int(self.global_x1), int(self.global_y1))
        if new_rect != self._last_sent_rect:
            self._last_sent_rect = new_rect
            if self.window.headerless_helper is not None:
                self.window.headerless_helper.set_maxi_rect(*new_rect)

    def _command_wrapper(self, btn, x, y):
        super()._command_wrapper(btn, x, y)
        if btn != 0:
            return
        self.window.is_maximized = not self.window.is_maximized
        self.refresh_maximize(self.window.is_maximized)

    def refresh_maximize(self, val):
        if not val:
            self.set_text('\uE922')
        else:
            self.set_text('\uE923')

    def draw_self(self, ctx: skia.Canvas):
        self._resize()
        super().draw_self(ctx)


class HeadContainer(Container, WindowHeaderWidgetMixin):
    def __init__(self, parent, **kw):
        Container.__init__(self, parent, **kw)
        WindowHeaderWidgetMixin.__init__(self)
        self.hovered_color = util.color_mix(self.bg_color, '#fff', 0.99)
        self.counter_paint.setStrokeWidth(2)
        self.on_hover(self._is_hovered)

    def _is_hovered(self, x, y):
        if self.window.headerless_helper is not None:
            self.window.headerless_helper.on_sysmenu = x < 32

    def _set_header(self, *_):
        super()._set_header()
        self.bg_paint.setColor(util.hex_str_to_int(self.hovered_color))

    def _reset_header(self, *_):
        super()._reset_header()
        self.bg_paint.setColor(util.hex_str_to_int(self.bg_color))

    def draw_self(self, ctx: skia.Canvas):
        r = skia.Rect(0, 0, self.width, self.height)
        if self.bg_paint:
            ctx.drawRect(r, self.bg_paint)
        if self.counter_paint:
            ctx.drawLine(0, self.height, self.width, self.height, self.counter_paint)



class Headered(WindowForPlatform):
    """Frameless GLFW Window with custom header with Windows style"""

    HEAD_HEIGHT = 32

    def __init__(self, width: int = 600, height: int = 400, title: str = 'someui'):
        super().__init__(width, height, title, True)

        self.set_size(*self.get_size())

        self.window_background = 0xff111111

        self.head = HeadContainer(self, bg='#111', is_rounded=False, counter_color='#2f2f2f')
        self.head.place(PlacingConfig(width=PlacementValue.relative(1.0), height=PlacementValue.fixed(self.HEAD_HEIGHT)))

        self.title = Label(self.head, text=title, background_color='#0000', align_x='center', align_y='center', font_size=12)
        self.title.hoverable = False
        self.title.clickable = False
        self.title.place(height=PlacementValue.relative(1.0))

        self.content = Container(self, bg='#111', counter=False, is_rounded=False)

        self.buttons = Container(self.head, counter=False, bg_enabled=False)
        self.buttons.debug = True
        self.buttons.place(height=PlacementValue.relative(1.0), anchor='right', x=PlacementValue.relative(1.0))
        self.buttons.mcfg.child_direction = PlacementDirection.ROW

        self.hide_btn = HeadButton(self.buttons, "\uE108", self.hide, font='Segoe MDL2 Assets', font_size=10,
                                hover_color='#2f2f2f', click_color='#1f1f1f', background_color=colors.TRANSPARENT)
        self.hide_btn.name = 'HideBTN'
        self.hide_btn.place(x=PlacementValue.auto(), width=PlacementValue.fixed(45), height=PlacementValue.fixed(self.HEAD_HEIGHT - 1))

        self.maximize_btn = MaximizeButton(self.buttons, font='Segoe MDL2 Assets', font_size=10,
                                hover_color='#2f2f2f', click_color='#1f1f1f', background_color=colors.TRANSPARENT)

        self.maximize_btn.place(x=PlacementValue.auto(), width=PlacementValue.fixed(45), height=PlacementValue.fixed(self.HEAD_HEIGHT - 1))

        self.close = HeadButton(self.buttons, "\uE8BB", self.destroy, font='Segoe MDL2 Assets', font_size=10,
                                hover_color='#d22', background_color=colors.TRANSPARENT, click_color='#a22', font_style=skia.FontStyle(0, 6, skia.FontStyle.kUpright_Slant))
        self.close.place(x=PlacementValue.auto(), width=PlacementValue.fixed(45), height=PlacementValue.fixed(self.HEAD_HEIGHT - 1))

        self._ready_content = True

        self.on_keyboard_press(self._toggle_recovery)

        def first_scene_rebuild():
            self._replace_content()

        self.on_scene_rebuild(first_scene_rebuild)

    def _replace_content(self):
        h = self.head.height if self.head.enabled else 0
        self.content.place(PlacingConfig(y=PlacementValue.fixed(h), width=PlacementValue.relative(1),
                                         height=PlacementValue(PlacementType.RELATIVE, 1.0, -h)))

    def _toggle_recovery(self, key_str, shift_state, ctrl_state, _):
        if shift_state and ctrl_state and key_str == '`':
            if self.head.enabled:
                self.disable()
            else:
                self.enable()

    def enable(self):
        if not self.head.enabled:
            self.head.enabled = True
            if self.headerless_helper:
                self.headerless_helper.enable()
            self._replace_content()

    def disable(self):
        if self.head.enabled:
            self.head.enabled = False
            if self.headerless_helper:
                self.headerless_helper.disable()
            self._replace_content()

    def set_title(self, title: str):
        super().set_title(title)
        self.title.set_text(title)

    def real(self):
        return self.content if hasattr(self, '_ready_content') else self