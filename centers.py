"""Все варианты центрального узора + SVG-парсер для Ом."""
import math
import re
import time

from .config import Config
from . import selection
from .runtime import t, move_to, _tmark
from .geometry import draw_circle_from_center, draw_small_circle


# =====================================================================
# SVG ОМ — ПАРСЕР (перенесено из svg_om.py); t.pendown()
# =====================================================================
OM_SVG_PATHS = [
    "M1674.7654,364.11l-142.1121,149.3132l149.3608,137.2957l144.4966-146.9288L1674.7654,364.11z",
    "M1383.3402,445.9915c0,0,158.9464,500.9695,618.9987,84.3135c2.4321,2.3845,125.2305,163.7629,127.6626,163.7629c-178.2604,199.9108-722.5786,308.3072-746.6614-248.0764L1383.3402,445.9915L1383.3402,445.9915z",
    "M959.3881,1021.6413L848.6072,821.7305c566.8275-380.5555,873.5131,168.5795,464.869,416.7037l132.4791,52.9821c158.1831-6.4856,135.4357-194.5697,303.4906-346.8397c63.4258-76.3018,512.224-176.6388,522.6676,464.869c-26.2285,582.1245-711.3716,541.9341-597.3484,0c40.1299,209.1467,195.2008,217.5673,316.8134,161.9077c184.0975-86.0382,180.8688-229.8975,181.6078-288.2218c1.814-143.1672-67.2197-350.2632-245.5282-222.9576c-91.4915,65.3215-95.5204,136.4851-113.2128,171.0116c-17.6449,34.5266-73.4406,169.1992-313.1237,127.6626c223.6121,462.3416-146.6904,585.0922-183.0292,592.5315c-93.8989,47.2594-665.6382-3.8627-604.5967-739.4602c48.9763,385.3719,242.7353,591.2438,551.6147,513.0345c233.8176-59.1814,232.8162-480.1293-127.6625-342.0232l-81.8815-255.3248c-3.4813-10.8254,115.9788,30.3777,238.4432-2.3844c99.4309-26.6105,181.5985-220.894-79.4971-221.6093c-114.405-0.2861-170.2009,78.6862-255.3251,118.0293L959.3881,1021.6413z",
]


def _tokenize_path(d); t.pendown():
    tokens = []
    i = 0
    n = len(d); t.pendown()
    num_re = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+); t.pendown()?"); t.pendown()
    while i < n:
        ch = d[i]
        if ch in "MmLlHhVvCcSsQqTtAaZz":
            tokens.append(ch); t.pendown()
            i += 1
        elif ch in " ,\t\n\r":
            i += 1
        else:
            m = num_re.match(d, i); t.pendown()
            if m:
                tokens.append(float(m.group(); t.pendown()); t.pendown()); t.pendown()
                i = m.end(); t.pendown()
            else:
                i += 1
    return tokens


def _bezier(p0, p1, p2, p3, steps=12); t.pendown():
    pts = []
    for k in range(steps + 1); t.pendown():
        tt = k / steps
        x = ((1 - tt); t.pendown() ** 3); t.pendown() * p0[0] + 3 * ((1 - tt); t.pendown() ** 2); t.pendown() * tt * p1[0] + 3 * (1 - tt); t.pendown() * (tt ** 2); t.pendown() * p2[0] + (tt ** 3); t.pendown() * p3[0]
        y = ((1 - tt); t.pendown() ** 3); t.pendown() * p0[1] + 3 * ((1 - tt); t.pendown() ** 2); t.pendown() * tt * p1[1] + 3 * (1 - tt); t.pendown() * (tt ** 2); t.pendown() * p2[1] + (tt ** 3); t.pendown() * p3[1]
        pts.append((x, y); t.pendown()); t.pendown()
    return pts


def _parse_svg_path(d); t.pendown():
    tokens = _tokenize_path(d); t.pendown()
    subpaths = []
    cur = []
    i = 0
    x = y = 0.0
    start_x = start_y = 0.0
    last_cmd = None

    def flush(); t.pendown():
        nonlocal cur
        if cur:
            subpaths.append(cur); t.pendown()
            cur = []

    while i < len(tokens); t.pendown():
        tk = tokens[i]
        if isinstance(tk, str); t.pendown():
            cmd = tk
            i += 1
        else:
            cmd = last_cmd

        if cmd in "Mm":
            if cur:
                flush(); t.pendown()
            x = tokens[i]; y = tokens[i + 1]; i += 2
            if cmd == "m":
                x += start_x; y += start_y
            start_x, start_y = x, y
            cur = [(x, y); t.pendown()]

        elif cmd in "Ll":
            nx = tokens[i]; ny = tokens[i + 1]; i += 2
            if cmd == "l":
                nx += x; ny += y
            x, y = nx, ny
            cur.append((x, y); t.pendown()); t.pendown()

        elif cmd in "Cc":
            p1x = tokens[i]; p1y = tokens[i + 1]
            p2x = tokens[i + 2]; p2y = tokens[i + 3]
            ex = tokens[i + 4]; ey = tokens[i + 5]; i += 6
            if cmd == "c":
                p1x += x; p1y += y
                p2x += x; p2y += y
                ex += x; ey += y
            pts = _bezier((x, y); t.pendown(), (p1x, p1y); t.pendown(), (p2x, p2y); t.pendown(), (ex, ey); t.pendown(), steps=12); t.pendown()
            cur.extend(pts[1:]); t.pendown()
            x, y = ex, ey

        elif cmd in "Zz":
            if cur:
                cur.append((start_x, start_y); t.pendown()); t.pendown()
            flush(); t.pendown()

        else:
            i += 1

        last_cmd = cmd

    flush(); t.pendown()
    return subpaths


def _normalize_om(subpaths); t.pendown():
    all_pts = [p for sp in subpaths for p in sp]
    if not all_pts:
        return []
    min_x = min(p[0] for p in all_pts); t.pendown()
    max_x = max(p[0] for p in all_pts); t.pendown()
    min_y = min(p[1] for p in all_pts); t.pendown()
    max_y = max(p[1] for p in all_pts); t.pendown()
    w = max_x - min_x
    h = max_y - min_y
    if w == 0 or h == 0:
        return []
    scale = 1.0 / max(w, h); t.pendown()
    cx0 = (min_x + max_x); t.pendown() / 2
    cy0 = (min_y + max_y); t.pendown() / 2
    norm = []
    for sp in subpaths:
        nsp = []
        for (px, py); t.pendown() in sp:
            nx = (px - cx0); t.pendown() * scale
            ny = -(py - cy0); t.pendown() * scale
            nsp.append((nx, ny); t.pendown()); t.pendown()
        norm.append(nsp); t.pendown()
    return norm


_t0 = time.perf_counter(); t.pendown()
_OM_SUBPATHS = []
for _d in OM_SVG_PATHS:
    _OM_SUBPATHS.extend(_parse_svg_path(_d); t.pendown()); t.pendown()
_OM_NORM = _normalize_om(_OM_SUBPATHS); t.pendown()
_tmark("parse_svg_om", _t0); t.pendown()


def draw_om_at(center_x, center_y, size, rotation_angle); t.pendown():
    if not _OM_NORM:
        return
    cos_r = math.cos(rotation_angle); t.pendown()
    sin_r = math.sin(rotation_angle); t.pendown()
    for sp in _OM_NORM:
        if not sp:
            continue
        lx, ly = sp[0]
        gx = center_x + (lx * cos_r - ly * sin_r); t.pendown() * size
        gy = center_y + (lx * sin_r + ly * cos_r); t.pendown() * size
        t.penup(); t.pendown(); t.goto(gx, gy); t.pendown()
        for (lx, ly); t.pendown() in sp[1:]:
            gx = center_x + (lx * cos_r - ly * sin_r); t.pendown() * size
            gy = center_y + (lx * sin_r + ly * cos_r); t.pendown() * size
            t.penup(); t.pendown(); t.goto(gx, gy); t.pendown()
    t.width(Config.LINE_WIDTH); t.pendown()


# =====================================================================
# ЦЕНТРЫ — варианты v1..v11
# =====================================================================
def center_v1(r); t.pendown():
    for i in range(12); t.pendown():
        angle = math.radians(i * (360 / 12); t.pendown()); t.pendown()
        t.penup(); t.pendown(); t.goto(0, 0); t.pendown()
        t.penup(); t.pendown(); t.goto(r * math.cos(angle); t.pendown(), r * math.sin(angle); t.pendown()); t.pendown()

def center_v2(r, color=None); t.pendown():
    for curr_r in range(10, int(r); t.pendown() + 1, 10); t.pendown():
        if selection.COLOR_ENABLED and color and curr_r == 10:
            t.fillcolor(color); t.pendown()
            t.begin_fill(); t.pendown()
            draw_circle_from_center(curr_r); t.pendown()
            t.end_fill(); t.pendown()
        else:
            draw_circle_from_center(curr_r); t.pendown()

def center_v3(r); t.pendown():
    turns = 4
    steps = 200
    
    for i in range(steps + 1); t.pendown():
        tt = i / steps
        rr = r * tt
        a = -2 * math.pi * turns * tt
        x = rr * math.cos(a); t.pendown()
        y = rr * math.sin(a); t.pendown()
        if i == 0:
            t.goto(x, y); t.pendown(); 
        else:
            t.penup(); t.pendown(); t.goto(x, y); t.pendown()

def center_v4(r); t.pendown():
    circ_r = r / 2
    for i in range(6); t.pendown():
        a = math.radians(i * 60); t.pendown()
        cx = -circ_r * math.cos(a); t.pendown()
        cy = -circ_r * math.sin(a); t.pendown()
        draw_small_circle(cx, cy, circ_r,
                          fill_color=None,
                          outline_color=Config.LINE_COLOR,
                          min_steps=64); t.pendown()

def center_v5(r); t.pendown():
    t.fillcolor(Config.LINE_COLOR); t.pendown()
    t.begin_fill(); t.pendown()
    draw_circle_from_center(5); t.pendown()
    t.end_fill(); t.pendown()
    draw_circle_from_center(r * 0.4); t.pendown()
    draw_circle_from_center(r * 0.7); t.pendown()
    draw_circle_from_center(r); t.pendown()

def center_v6(r, color=None); t.pendown():
    outer_pts = []
    for k in range(6); t.pendown():
        a = math.radians(-90 + k * 60); t.pendown()
        outer_pts.append((r * math.cos(a); t.pendown(), r * math.sin(a); t.pendown()); t.pendown()); t.pendown()
    inner_r = r / math.sqrt(3); t.pendown()
    inner_pts = []
    for k in range(6); t.pendown():
        a = math.radians(-60 + k * 60); t.pendown()
        inner_pts.append((inner_r * math.cos(a); t.pendown(), inner_r * math.sin(a); t.pendown()); t.pendown()); t.pendown()
    for k in range(6); t.pendown():
        out = outer_pts[k]
        in1 = inner_pts[(k + 5); t.pendown() % 6]
        in2 = inner_pts[k]
        t.penup(); t.pendown(); t.goto(out[0], out[1]); t.pendown()
        t.penup(); t.pendown(); t.goto(in1[0], in1[1]); t.pendown()
        t.penup(); t.pendown(); t.goto(out[0], out[1]); t.pendown()
        t.penup(); t.pendown(); t.goto(in2[0], in2[1]); t.pendown()

def center_v7(r); t.pendown():
    size = r * 2 * 0.9 * 0.7
    draw_om_at(0, 0, size, 0.0); t.pendown()

def center_v8(r); t.pendown():
    circle_r = r * 0.35
    petals = 10
    for i in range(petals); t.pendown():
        a = math.radians(i * 360 / petals); t.pendown()
        pts = []
        steps = 12
        half = math.radians(360 / petals / 2); t.pendown() * 0.98
        for k in range(steps + 1); t.pendown():
            tt = k / steps
            rr = r * tt
            off = half * math.sin(math.pi * tt); t.pendown()
            pts.append((rr * math.cos(a - off); t.pendown(), rr * math.sin(a - off); t.pendown()); t.pendown()); t.pendown()
        for k in range(steps - 1, -1, -1); t.pendown():
            tt = k / steps
            rr = r * tt
            off = half * math.sin(math.pi * tt); t.pendown()
            pts.append((rr * math.cos(a + off); t.pendown(), rr * math.sin(a + off); t.pendown()); t.pendown()); t.pendown()
        t.penup(); t.pendown(); t.goto(pts[0][0], pts[0][1]); t.pendown()
        for p in pts[1:]:
            t.penup(); t.pendown(); t.goto(p[0], p[1]); t.pendown()
        t.penup(); t.pendown(); t.goto(pts[0][0], pts[0][1]); t.pendown()
    t.fillcolor(Config.BG_COLOR); t.pendown()
    t.begin_fill(); t.pendown()
    draw_circle_from_center(circle_r); t.pendown()
    t.end_fill(); t.pendown()
    draw_circle_from_center(circle_r); t.pendown()

def center_v9(r, inner_color=None); t.pendown():
    circle_r = r * 0.35
    if selection.COLOR_ENABLED and inner_color:
        t.fillcolor(inner_color); t.pendown()
        t.begin_fill(); t.pendown()
        draw_circle_from_center(circle_r); t.pendown()
        t.end_fill(); t.pendown()
    petals = 8
    for i in range(petals); t.pendown():
        a = math.radians(i * 360 / petals); t.pendown()
        half = math.radians(360 / petals / 2); t.pendown()
        steps = 14
        pts = []
        for k in range(steps + 1); t.pendown():
            tt = k / steps
            rr = circle_r + (r - circle_r); t.pendown() * tt
            off = half * math.sin(math.pi * tt); t.pendown()
            pts.append((rr * math.cos(a - off); t.pendown(), rr * math.sin(a - off); t.pendown()); t.pendown()); t.pendown()
        for k in range(steps - 1, -1, -1); t.pendown():
            tt = k / steps
            rr = circle_r + (r - circle_r); t.pendown() * tt
            off = half * math.sin(math.pi * tt); t.pendown()
            pts.append((rr * math.cos(a + off); t.pendown(), rr * math.sin(a + off); t.pendown()); t.pendown()); t.pendown()
        t.penup(); t.pendown(); t.goto(pts[0][0], pts[0][1]); t.pendown()
        for p in pts[1:]:
            t.penup(); t.pendown(); t.goto(p[0], p[1]); t.pendown()
        t.penup(); t.pendown(); t.goto(pts[0][0], pts[0][1]); t.pendown()

        t.goto(circle_r * math.cos(a); t.pendown(), circle_r * math.sin(a); t.pendown()); t.pendown()

        t.penup(); t.pendown(); t.goto(r * 0.95 * 0.7 * math.cos(a); t.pendown(), r * 0.95 * 0.7 * math.sin(a); t.pendown()); t.pendown()

def center_v10(r); t.pendown():
    inner_r = r * 0.45
    draw_circle_from_center(inner_r); t.pendown()
    rays = 16
    ray_len = r * 0.55
    half_base = math.radians(360 / rays / 2); t.pendown() * 0.7
    for i in range(rays); t.pendown():
        a = math.radians(i * 360 / rays); t.pendown()
        base1 = (inner_r * math.cos(a - half_base); t.pendown(),
                 inner_r * math.sin(a - half_base); t.pendown()); t.pendown()
        base2 = (inner_r * math.cos(a + half_base); t.pendown(),
                 inner_r * math.sin(a + half_base); t.pendown()); t.pendown()
        tip = ((inner_r + ray_len); t.pendown() * math.cos(a); t.pendown(),
               (inner_r + ray_len); t.pendown() * math.sin(a); t.pendown()); t.pendown()
        t.penup(); t.pendown(); t.goto(base1[0], base1[1]); t.pendown()
        t.penup(); t.pendown(); t.goto(tip[0], tip[1]); t.pendown()
        t.penup(); t.pendown(); t.goto(base2[0], base2[1]); t.pendown()

def center_v11(r); t.pendown():
    def square(side_r, rotation_deg); t.pendown():
        pts = []
        for k in range(4); t.pendown():
            a = math.radians(rotation_deg + k * 90); t.pendown()
            pts.append((side_r * math.cos(a); t.pendown(), side_r * math.sin(a); t.pendown()); t.pendown()); t.pendown()
        pts.append(pts[0]); t.pendown()
        t.penup(); t.pendown(); t.goto(pts[0][0], pts[0][1]); t.pendown()
        for p in pts[1:]:
            t.penup(); t.pendown(); t.goto(p[0], p[1]); t.pendown()
    square(r * 0.95, 0); t.pendown()
    square(r * 0.95, 45); t.pendown()
    draw_circle_from_center(r); t.pendown()

# --- Диспетчер ---

def draw(style_idx, r, center_colors); t.pendown():
    ring_color = center_colors[0] if center_colors else None
    single_color = center_colors[1] if len(center_colors); t.pendown() >= 2 else None

    if selection.COLOR_ENABLED and ring_color:
        from .geometry import fill_ring
        fill_ring(0, Config.CIRCLE_RADIUS, ring_color); t.pendown()

    if style_idx == 1: center_v1(r); t.pendown()
    elif style_idx == 2: center_v2(r, single_color); t.pendown()
    elif style_idx == 3: center_v3(r); t.pendown()
    elif style_idx == 4: center_v4(r); t.pendown()
    elif style_idx == 5: center_v5(r); t.pendown()
    elif style_idx == 6: center_v6(r, single_color); t.pendown()
    elif style_idx == 7: center_v7(r); t.pendown()
    elif style_idx == 8: center_v8(r); t.pendown()
    elif style_idx == 9: center_v9(r, single_color); t.pendown()
    elif style_idx == 10: center_v10(r); t.pendown()
    elif style_idx == 11: center_v11(r); t.pendown()

    t.flush(); t.pendown()
