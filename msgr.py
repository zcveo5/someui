import skia

from someui import GLFWWindow, Button, Label, Container, Event, hex_str_to_int


class Entry(Button):
    _focus_change = Event()

    def __init__(self, parent, start_value='', on_change=None, on_focus=None, on_enter=None,
                 font='Inter', font_size=14, background_color='white', text_color='black', placeholder='Entry',
                 focus_color='#8080ff', idle_color='black', debug=False, debug_label=False):
        super().__init__(parent, font=font, font_size=font_size, background_color=background_color, text_color=text_color, debug=debug_label)
        self.focus_color = focus_color
        self.idle_color = idle_color
        self._debug_entry = debug
        self._value = start_value
        self._placeholder = placeholder
        self._placeholder_blob = None
        self.on_change = Event(on_change)
        self.on_focus = Event(on_focus)
        self.on_enter = Event(on_enter)
        self._is_focused = False
        self.window.on_keyboard_write(self._key_enter_wrapper)
        self._update_text()
        self._focus_change(self._check_focus)

        self.text_cursor_paint = skia.Paint(hex_str_to_int(text_color))
        self.text_cursor_paint.setStyle(skia.Paint.kStroke_Style)
        self.text_cursor_paint.setStrokeWidth(2)
        self.text_cursor_paint.setStrokeCap(skia.Paint.kRound_Cap)
        self.text_cursor_paint.setStrokeJoin(skia.Paint.kRound_Join)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self._update_text()

    def _check_focus(self, instance):
        if instance is self:
            self._is_focused = True
            self.counter_paint.setColor(hex_str_to_int(self.focus_color))
        else:
            self._is_focused = False
            self.counter_paint.setColor(hex_str_to_int(self.idle_color))

    @property
    def placeholder(self):
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value):
        self._placeholder = value
        self._placeholder_blob = None

    def _command_wrapper(self, btn, x, y):
        if self._debug_entry:
            print(f'{self} got focus')
        self._focus_change.process(self)
        self._update_text()
        super()._command_wrapper(btn, x, y)

    def _update_text(self):
        if self._value.strip():
            self.set_text(self._value)
            self.text_paint.setAlpha(255)
        else:
            self.set_text(self._placeholder)
            self.text_paint.setAlpha(127)

    def _key_enter_wrapper(self, key: str, shift, ctrl, alt):
        if not self._is_focused:
            return

        if len(key) == 1:
            if not shift:
                key = key.lower()
            self._value += key
        else:
            if key == 'BACKSPACE':
                self._value = self._value[:-1]
            elif key == 'SPACE':
                self._value += ' '
            elif key == 'ENTER':
                self.on_enter.process(self._value)
            elif key == 'ESCAPE':
                self._focus_change.process(None)
                return
        self.on_change.process(self._value)
        self._update_text()

    def draw_self(self, ctx: skia.Canvas):
        super().draw_self(ctx)
        if self._is_focused:
            ctx.drawLine(self._text_x_offset + self._raw_text_w, self._raw_text_h - self._text_y_offset,
                     self._text_x_offset + self._raw_text_w, self._raw_text_h, self.text_cursor_paint)


if __name__ == '__main__':
    window = GLFWWindow(640, 480)
    window.window_background = 0xffffffff

    entry = Entry(window, debug=True)
    entry.place(y='auto')

    window.mainloop()