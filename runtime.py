"""Рисование на Cairo: векторное окно и векторный PDF.

Модуль повторяет API turtle (goto / penup / pendown / begin_fill /
fill_color / circle ...), поэтому модули стилей работают без изменений.
Сцена хранит векторные операции: она же рисуется в окне (через Cairo,
со сглаживанием) и она же пишется в PDF — без Ghostscript.
"""
import math
import os
import time

# cairocffi ищет libcairo в стандартных путях; на macOS она из Homebrew.
_LIB_DIRS = ("/opt/homebrew/lib", "/usr/local/lib")
_found = [d for d in _LIB_DIRS if os.path.exists(os.path.join(d, "libcairo.2.dylib"))]
if _found:
    _old = os.environ.get("DYLD_LIBRARY_PATH", "")
    if _found[0] not in _old:
        os.environ["DYLD_LIBRARY_PATH"] = os.pathsep.join(_found + ([_old] if _old else []))

import cairocffi as cairo          # noqa: E402
from PIL import Image, ImageColor, ImageTk   # noqa: E402
import tkinter as tk               # noqa: E402

from .config import Config         # noqa: E402
from .traj import Line, Arc, Bezier, FillElement, TrajectoryElement  # noqa: E402


W = Config.WINDOW_SIZE


def _rgb(color):
    """Цвет turtle -> (r, g, b) в долях единицы."""
    if color is None:
        return (0.0, 0.0, 0.0)
    if isinstance(color, (tuple, list)):
        try:
            return tuple(float(c) / 255.0 for c in list(color)[:3])
        except (TypeError, ValueError):
            # Если в списке оказались строки, пытаемся обработать через ImageColor
            try:
                r, g, b = ImageColor.getrgb(str(color))[:3]
                return r / 255.0, g / 255.0, b / 255.0
            except Exception:
                return (0.0, 0.0, 0.0)
    try:
        r, g, b = ImageColor.getrgb(str(color))[:3]
    except Exception:
        r, g, b = 0, 0, 0
    return r / 255.0, g / 255.0, b / 255.0


class AnimationManager:
    """Управляет прогрессом рисования всей траектории с постоянной скоростью."""
    def __init__(self, speed_px_s):
        self.speed_px_s = speed_px_s
        self.trajectory = []
        self.total_length = 0.0
        self.start_time = None

    def add_element(self, element):
        self.trajectory.append(element)
        self.total_length += element.length

    def reset(self):
        self.start_time = None

    def get_current_state(self):
        """Возвращает список (элемент, прогресс), который нужно отрисовать."""
        if not self.trajectory:
            return []

        if self.start_time is None:
            self.start_time = time.perf_counter()

        elapsed = time.perf_counter() - self.start_time
        dist_covered = elapsed * self.speed_px_s

        final_state = []
        running_len = 0.0
        for elem in self.trajectory:
            if running_len >= dist_covered:
                if elem.length == 0:
                    final_state.append((elem, 1.0))
                else:
                    break

            if running_len + elem.length <= dist_covered:
                final_state.append((elem, 1.0))
            else:
                t = (dist_covered - running_len) / elem.length if elem.length > 0 else 1.0
                final_state.append((elem, min(1.0, t)))
                break
            running_len += elem.length

        return final_state

class Scene:
    """Векторные операции рисунка: штрихи и заливки."""

    def __init__(self):
        self.ops = []

    def add_stroke(self, paths, color, width):
        if paths:
            self.ops.append(('stroke', paths, _rgb(color), float(width)))

    def add_fill(self, paths, color):
        if paths:
            self.ops.append(('fill', paths, _rgb(color)))

    @staticmethod
    def _build_path(cr, paths):
        for path in paths:
            if isinstance(path, tuple) and path and path[0] == 'arc':
                if len(path) == 6:
                    _, cx, cy, r, a0, a1 = path
                    cr.new_sub_path()
                    cr.arc(cx, cy, r, a0, a1)
                    continue
                _, cx, cy, r = path
                cr.new_sub_path()
                cr.arc(cx, cy, r, 0.0, 2.0 * math.pi)
                cr.close_path()
                continue
            pts = path
            if len(pts) < 2:
                continue
            cr.move_to(pts[0][0], pts[0][1])
            for x, y in pts[1:]:
                cr.line_to(x, y)

    @classmethod
    def render_ops(cls, cr, ops):
        cr.save()
        cr.translate(W / 2.0, W / 2.0)
        cr.scale(1.0, -1.0)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        for op in ops:
            if op[0] == 'stroke':
                _, paths, rgb, width = op
                cr.set_source_rgb(*rgb)
                cr.set_line_width(max(width, 0.1))
                cr.new_path()
                cls._build_path(cr, paths)
                cr.stroke()
            else:
                _, paths, rgb = op
                cr.set_source_rgb(*rgb)
                cr.new_path()
                cls._build_path(cr, paths)
                cr.fill()
        cr.restore()

    def render(self, cr):
        self.render_ops(cr, self.ops)


class CairoTurtle:
    """Черепаха, записывающая траекторию в AnimationManager и Scene."""

    def __init__(self, scene, anim_manager):
        self.scene = scene
        self.anim_manager = anim_manager
        self._x = 0.0
        self._y = 0.0
        self._heading = 0.0
        self._down = True
        self._color = "black"
        self._fillcolor = "black"
        self._width = Config.LINE_WIDTH
        self._filling = False
        self._fill_paths = []
        self._fill_cur = None
        self._deferred = []

    def pos(self):
        return (self._x, self._y)

    def isdown(self):
        return self._down

    def filling(self):
        return self._filling

    def pencolor(self, color=None):
        if color is not None:
            self._color = color
        return self._color

    def fillcolor(self, color=None):
        if color is not None:
            self._fillcolor = color
        return self._fillcolor

    def width(self, w=None):
        if w is not None:
            self._width = w
        return self._width

    def setheading(self, angle):
        self._heading = math.radians(angle)

    def speed(self, *args):
        return None

    def hideturtle(self):
        return None

    def showturtle(self):
        return None

    def penup(self):
        self._down = False

    def pendown(self):
        self._down = True

    def flush(self):
        pass

    def goto(self, x, y=None):
        if y is None:
            x, y = x[0], x[1]
        x = float(x)
        y = float(y)

        if self._down:
            # Используем Config.LINE_WIDTH если текущая ширина подозрительно мала или не задана
            current_w = self._width if self._width >= 0.5 else Config.LINE_WIDTH
            self.anim_manager.add_element(Line(
                (self._x, self._y), (x, y),
                color=self._color, width=current_w
            ))
            self.scene.add_stroke([[(self._x, self._y), (x, y)]], self._color, current_w)

        self._x, self._y = x, y

        if self._filling:
            if self._fill_cur is None:
                self._fill_cur = [(x, y)]
            else:
                self._fill_cur.append((x, y))

    def circle(self, radius, extent=None, steps=None):
        r = abs(float(radius))
        if r <= 0:
            return

        cx = self._x - r * math.sin(self._heading)
        cy = self._y + r * math.cos(self._heading)

        if self._down:
            a0 = 0.0
            a1 = math.radians(extent) if extent is not None else 2.0 * math.pi

            current_w = self._width if self._width >= 0.5 else Config.LINE_WIDTH

            self.anim_manager.add_element(Arc(
                cx, cy, r, a0, a1,
                color=self._color, width=current_w
            ))
            self.scene.add_stroke([('arc', cx, cy, r, a0, a1)], self._color, current_w)

            self._x = cx + r * math.cos(a1)
            self._y = cy + r * math.sin(a1)

        if self._filling:
            if self._fill_cur and len(self._fill_cur) > 2:
                self._fill_paths.append(self._fill_cur)
            self._fill_paths.append(('arc', cx, cy, r))
            self._fill_cur = None

    def begin_fill(self):
        self._filling = True
        self._fill_paths = []
        self._fill_cur = []
        self._deferred = []

    def end_fill(self):
        if self._filling:
            if self._fill_cur and len(self._fill_cur) > 2:
                paths = self._fill_paths + [self._fill_cur]
            else:
                paths = self._fill_paths

            self.anim_manager.add_element(FillElement(
                paths, self._fillcolor
            ))
            self.scene.add_fill(paths, self._fillcolor)

        self._filling = False
        self._fill_paths = []
        self._fill_cur = None

class Screen:
    """Окно с векторной сценой (Cairo рисует со сглаживанием)."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mandala Generator")
        self.canvas = tk.Canvas(self.root, width=W, height=W,
                                bg=Config.BG_COLOR, highlightthickness=0)
        self.canvas.pack()

        self.anim_manager = AnimationManager(Config._speed_px_s if hasattr(Config, '_speed_px_s') else 500.0)
        self.scene = Scene()
        self.turtle = CairoTurtle(self.scene, self.anim_manager)

        self._base = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, W)
        self._paint_base()
        self._photo = None
        self._item = None
        self._frame = None

    def _paint_base(self):
        cr = cairo.Context(self._base)
        r, g, b = _rgb(Config.BG_COLOR)
        cr.set_source_rgb(r, g, b)
        cr.paint()

    def bgcolor(self, *args): return None
    def title(self, *args): return None
    def setup(self, *args, **kwargs): return None
    def delay(self, *args): return None
    def tracer(self, *args): return None

    def bye(self):
        self._photo = None
        try:
            self.root.destroy()
        except Exception:
            pass

    def done(self):
        self.update()
        self.root.mainloop()

    def update(self):
        try:
            if self._frame is None:
                self._frame = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, W)

            fc = cairo.Context(self._frame)
            r, g, b = _rgb(Config.BG_COLOR)
            fc.set_source_rgb(r, g, b)
            fc.paint()

            fc.translate(W / 2.0, W / 2.0)
            fc.scale(1.0, -1.0)
            fc.set_line_cap(cairo.LINE_CAP_ROUND)
            fc.set_line_join(cairo.LINE_JOIN_ROUND)
            fc.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)

            current_state = self.anim_manager.get_current_state()

            for elem, t in current_state:
                if isinstance(elem, FillElement):
                    fc.set_source_rgb(*_rgb(elem.fill_color))
                    Scene._build_path(fc, elem.paths)
                    fc.fill()
                    continue

                # Каждый элемент рисуется своим путем. Это медленнее, но
                # гарантирует, что все детали будут на своих местах.
                fc.new_path()
                fc.set_source_rgb(*_rgb(elem.color))
                fc.set_line_width(Config.LINE_WIDTH)

                if isinstance(elem, Line):
                    p1, p2 = elem.p1, elem.get_point(t)
                    fc.move_to(*p1)
                    fc.line_to(*p2)
                elif isinstance(elem, Arc):
                    angle_end = elem.a0 + t * (elem.a1 - elem.a0)
                    start_pt = (elem.cx + elem.r * math.cos(elem.a0),
                                elem.cy + elem.r * math.sin(elem.a0))
                    fc.move_to(*start_pt)
                    fc.arc(elem.cx, elem.cy, elem.r, elem.a0, angle_end)
                elif isinstance(elem, Bezier):
                    pts = [elem.get_point((i/20)*t) for i in range(21)]
                    fc.move_to(*pts[0])
                    for p in pts[1:]: fc.line_to(*p)

                fc.stroke()

            img = Image.frombytes('RGBA', (W, W), bytes(self._frame.get_data()), 'raw', 'BGRA', self._frame.get_stride())
            self._photo = ImageTk.PhotoImage(img)
            if self._item is None:
                self._item = self.canvas.create_image(0, 0, anchor='nw', image=self._photo)
            else:
                self.canvas.itemconfigure(self._item, image=self._photo)
            self.root.update_idletasks()
            self.root.update()
        except Exception as exc:
            print(f"Update error: {exc}")



screen = Screen()
scene = screen.scene
t = screen.turtle
t.width(Config.LINE_WIDTH)

def _tmark(label, t0):
    if not hasattr(Config, 'TIMING_ENABLED') or not Config.TIMING_ENABLED:
        return
    dt = time.perf_counter() - t0
    if '_timings' not in globals():
        globals()['_timings'] = []
    globals()['_timings'].append((label, dt))

def _timing_report():
    """Генерирует отчет по замеренным фазам рисования."""
    if not hasattr(Config, 'TIMING_ENABLED') or not Config.TIMING_ENABLED:
        return ""
    timings = globals().get('_timings', [])
    if not timings:
        return ""
    lines = ["", "----- Тайминги фаз -----"]
    total = 0.0
    for label, dt in timings:
        lines.append(f"[timing] {label:<24} {dt:6.3f} s")
        total += dt
    lines.append(f"[timing] {'TOTAL (сумма фаз)':<24} {total:6.3f} s")
    lines.append("------------------------")
    return "\n".join(lines) + "\n"

def speed_px_s():
    return screen.anim_manager.speed_px_s

def apply_draw_speed(level):
    ratio = Config.SPEED_FAST_PX_S / Config.SPEED_SLOW_PX_S
    new_speed = Config.SPEED_SLOW_PX_S * ratio ** ((max(1, min(20, int(level))) - 1) / 19.0)
    screen.anim_manager.speed_px_s = new_speed
    screen.anim_manager.reset()
    print(f"--- Target Speed: {new_speed:.2f} px/s ---")

def move_to(x, y):
    t.goto(x, y)

def done():
    def animate():
        screen.update()
        screen.root.after(16, animate)
    animate()
    screen.root.mainloop()

def bye():
    screen.bye()
