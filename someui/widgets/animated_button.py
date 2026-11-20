import skia
from someui.widgets.button import Button
from someui.util import lerp_color_argb, are_colors_close_argb, hex_str_to_int


class PrettyButton(Button):
    def __init__(self, parent, text = '', command=None, font=None, font_size=None, typeface: skia.Typeface | None = None,
                 text_color=None, background_color=None, click_color=None, hover_color=None, debug=False, font_style=None):
        super().__init__(parent, text, command, font, font_size, typeface, text_color, background_color, click_color, hover_color, debug, font_style)

        self._target_color = hex_str_to_int(self._bg_color)
        self._current_color = hex_str_to_int(self._bg_color)
        self._running = False

        self._active_paint = skia.Paint(self._current_color)

    def _frame(self, dt):
        new_color = lerp_color_argb(self._current_color, self._target_color, 0.2)
        self._current_color = new_color
        self._active_paint.setColor(new_color)

        if are_colors_close_argb(self._current_color, self._target_color):
            self._current_color = self._target_color
            self.window.on_animation_frame.remove(self._frame)
            self._running = False

    def _run_anim(self, clr):
        self._target_color = clr
        if not self._running:
            self._running = True
            self.window.on_animation_frame(self._frame)

    def _set_color(self):
        if self.held:
            clr = self._click_color
        elif self.hovered:
            clr = self._hover_color
        else:
            clr = self._bg_color

        self._run_anim(hex_str_to_int(clr))