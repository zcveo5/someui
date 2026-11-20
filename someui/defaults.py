import skia

from someui.util import Defaults
from someui.paint_registry import Registry

DEBUG_FONT = skia.Font(skia.Typeface(), 14)
DEBUG_RED = skia.Paint(skia.ColorRED)
DEBUG_RED_A = skia.Paint(skia.ColorRED)
DEBUG_RED_A.setAlpha(100)
DEBUG_BLACK = skia.Paint(skia.ColorBLACK)

RootDefaults = Defaults('#888', '#fff', 'Inter', 14)
RootPaints: Registry = Registry(RootDefaults)