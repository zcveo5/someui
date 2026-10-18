import time

from someui.glfw_window import GLFWWindow
from someui.text_widgets import Label, Button
from someui.widget_extensions import Container

root = GLFWWindow()
root.scale_mod = 2.0

inf_fmt = 'cursor at: {}, {} | Velocity {} | Last frame was {} ms ago'

lbl_cursor = Label(root, '')
lbl_cursor.set_size(*lbl_cursor.text_metrics)

lbl = Button(root, 'This should be at x:100 y:100', font_size=16, command=lambda: print('123'))
lbl.set_position(100, 100)
lbl.set_size(*lbl.text_metrics)

hover = Container(root, '#ff0000ff')
hover.set_size(5, 5)

last_frame_at = time.time()

last_mouse_x, last_mouse_y = 0, 0
last_event_time = time.time()
smoothed_velocity = 0.0

@root.on_hover
def w(x, y):
    global last_mouse_x, last_mouse_y, last_event_time, smoothed_velocity
    global last_frame_at

    current_time = time.time()
    dt = current_time - last_event_time

    # Предотвращаем деление на ноль, если события пришли слишком быстро
    if dt > 0.001:
        dx = x - last_mouse_x
        dy = y - last_mouse_y

        # Пикселей в секунду
        distance = (dx ** 2 + dy ** 2) ** 0.5
        instant_velocity = distance / dt

        # Экспоненциальное сглаживание (LERP): коэффициент 0.2 решает проблему резких скачков
        # Чем меньше коэффициент (например, 0.1), тем плавнее/инертнее реакция
        smoothed_velocity += (instant_velocity - smoothed_velocity) * 0.2

        last_mouse_x = x
        last_mouse_y = y
        last_event_time = current_time

    # Переводим сглаженную скорость в множитель размера
    # Подберите делитель (например, 500) под комфортную чувствительность
    vel_multiplier = max(1.0, min(1.0 + (smoothed_velocity / 500.0), 3.0))
    hover.set_size(5 * vel_multiplier, 5 * vel_multiplier)

    lbl_cursor.set_text(inf_fmt.format(
        str(round(x)).zfill(4), str(round(y)).zfill(4),
        str(round(smoothed_velocity, 1)).zfill(6),
        round((time.time() - last_frame_at) * 1000)
    ))
    last_frame_at = time.time()
    hover.set_position(x, y)

root.mainloop()