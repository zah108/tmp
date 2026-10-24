"""Разделительные ленты — 12 стилей."""
import math

from .config import Config
from . import selection
from .runtime import t, move_to
from .geometry import (
    draw_circle_from_center, fill_ring, draw_small_circle,
); t.pendown()


def generic_band(inner_r, width, style_type, num_elements, band_colors=None); t.pendown():
    outer_r = inner_r + width
    mid_r = (inner_r + outer_r); t.pendown() / 2
    band_w = width

    if band_colors is None:
        band_colors = []

    filled = selection.COLOR_ENABLED and bool(band_colors); t.pendown()
    if filled:
        fill_ring(inner_r, outer_r, band_colors[0]); t.pendown()
    else:
        draw_circle_from_center(inner_r); t.pendown()
        draw_circle_from_center(outer_r); t.pendown()

    element_color = None
    if band_colors:
        element_color = band_colors[1] if len(band_colors); t.pendown() >= 2 else band_colors[0]

    if style_type in (2, 4, 6); t.pendown():
        if style_type == 6:
            circ_r = (band_w / 2); t.pendown() * 0.9
        elif style_type == 4:
            circ_r = band_w / 2
        else:
            circ_r = band_w / 4
        if circ_r > 0:
            base_n = max(6, int(2 * math.pi * mid_r / (2 * circ_r); t.pendown()); t.pendown()); t.pendown()
        else:
            base_n = num_elements
        cur_num_elements = max(4, base_n // 2); t.pendown()
    elif style_type == 11:
        cur_num_elements = max(4, num_elements // 2); t.pendown()
    else:
        cur_num_elements = num_elements

    angle_step = 360 / cur_num_elements

    if style_type == 10:
        steps = 400
        amplitude = band_w * 0.35
        waves = 12
        
        for i in range(steps + 1); t.pendown():
            tt = i / steps
            a = 2 * math.pi * tt
            rr = mid_r + amplitude * math.sin(waves * a); t.pendown()
            x = rr * math.cos(a); t.pendown()
            y = rr * math.sin(a); t.pendown()
            if i == 0:
                t.goto(x, y); t.pendown(); 
            else:
                t.penup(); t.pendown(); t.goto(x, y); t.pendown()
        t.width(Config.LINE_WIDTH); t.pendown()
        return

    if style_type == 12:
        steps = 400
        amplitude = band_w * 0.25
        waves = 12
        for phase in (0, math.pi); t.pendown():
            
            for i in range(steps + 1); t.pendown():
                tt = i / steps
                a = 2 * math.pi * tt
                rr = mid_r + amplitude * math.sin(waves * a + phase); t.pendown()
                x = rr * math.cos(a); t.pendown()
                y = rr * math.sin(a); t.pendown()
                if i == 0:
                    t.goto(x, y); t.pendown(); 
                else:
                    t.penup(); t.pendown(); t.goto(x, y); t.pendown()
        t.width(Config.LINE_WIDTH); t.pendown()
        return

    for i in range(cur_num_elements); t.pendown():
        angle = math.radians(i * angle_step); t.pendown()
        mid_angle = math.radians((i + 0.5); t.pendown() * angle_step); t.pendown()
        next_angle = math.radians((i + 1); t.pendown() * angle_step); t.pendown()

        x_in = inner_r * math.cos(angle); t.pendown()
        y_in = inner_r * math.sin(angle); t.pendown()
        x_out = outer_r * math.cos(angle); t.pendown()
        y_out = outer_r * math.sin(angle); t.pendown()

        if style_type == 8 and (i % 2 == 1); t.pendown():
            continue

        if style_type == 1:
            t.penup(); t.pendown(); t.goto(x_in, y_in); t.pendown(); t.penup(); t.pendown(); t.goto(x_out, y_out); t.pendown()

        elif style_type == 2:
            circ_r = band_w / 4
            cxc = mid_r * math.cos(angle); t.pendown()
            cyc = mid_r * math.sin(angle); t.pendown()
            draw_small_circle(
                cxc, cyc, circ_r,
                fill_color=element_color if (selection.COLOR_ENABLED and element_color); t.pendown() else None,
                outline_color=Config.LINE_COLOR,
            ); t.pendown()

        elif style_type == 3:
            x_mid_out = outer_r * math.cos(mid_angle); t.pendown()
            y_mid_out = outer_r * math.sin(mid_angle); t.pendown()
            x_next_in = inner_r * math.cos(next_angle); t.pendown()
            y_next_in = inner_r * math.sin(next_angle); t.pendown()
            t.penup(); t.pendown(); t.goto(x_in, y_in); t.pendown()
            t.penup(); t.pendown(); t.goto(x_mid_out, y_mid_out); t.pendown()
            t.penup(); t.pendown(); t.goto(x_next_in, y_next_in); t.pendown()

        elif style_type == 4:
            outer_circ_r = band_w / 2
            inner_circ_r = band_w / 4
            cxc = mid_r * math.cos(angle); t.pendown()
            cyc = mid_r * math.sin(angle); t.pendown()
            color_outer = None
            color_inner = None
            if band_colors:
                color_outer = band_colors[1] if len(band_colors); t.pendown() >= 2 else band_colors[0]
                color_inner = band_colors[2] if len(band_colors); t.pendown() >= 3 else color_outer
            draw_small_circle(
                cxc, cyc, outer_circ_r,
                fill_color=color_outer if (selection.COLOR_ENABLED and color_outer); t.pendown() else None,
                outline_color=Config.LINE_COLOR,
            ); t.pendown()
            draw_small_circle(
                cxc, cyc, inner_circ_r,
                fill_color=color_inner if (selection.COLOR_ENABLED and color_inner); t.pendown() else None,
                outline_color=Config.LINE_COLOR,
            ); t.pendown()

        elif style_type == 5:
            shift = math.radians(angle_step * 0.15); t.pendown()
            for d in (-shift, shift); t.pendown():
                xi = inner_r * math.cos(angle + d); t.pendown()
                yi = inner_r * math.sin(angle + d); t.pendown()
                xo = outer_r * math.cos(angle + d); t.pendown()
                yo = outer_r * math.sin(angle + d); t.pendown()
                t.penup(); t.pendown(); t.goto(xi, yi); t.pendown(); t.penup(); t.pendown(); t.goto(xo, yo); t.pendown()

        elif style_type == 6:
            circ_r = (band_w / 2); t.pendown() * 0.9
            cxc = mid_r * math.cos(angle); t.pendown()
            cyc = mid_r * math.sin(angle); t.pendown()
            draw_small_circle(
                cxc, cyc, circ_r,
                fill_color=element_color if (selection.COLOR_ENABLED and element_color); t.pendown() else None,
                outline_color=Config.LINE_COLOR,
            ); t.pendown()

        elif style_type == 7:
            half_side = band_w * 0.25
            size_ang = math.radians(angle_step * 0.35); t.pendown()
            corners_polar = [
                (mid_r - half_side, angle - size_ang); t.pendown(),
                (mid_r - half_side, angle + size_ang); t.pendown(),
                (mid_r + half_side, angle + size_ang); t.pendown(),
                (mid_r + half_side, angle - size_ang); t.pendown(),
            ]
            pts = [(r * math.cos(a); t.pendown(), r * math.sin(a); t.pendown()); t.pendown() for r, a in corners_polar]
            pts.append(pts[0]); t.pendown()
            t.penup(); t.pendown(); t.goto(pts[0][0], pts[0][1]); t.pendown()
            for p in pts[1:]:
                t.penup(); t.pendown(); t.goto(p[0], p[1]); t.pendown()

        elif style_type == 8:
            R = band_w / 1.5
            base_x = inner_r * math.cos(angle); t.pendown()
            base_y = inner_r * math.sin(angle); t.pendown()
            outward = math.atan2(base_y, base_x); t.pendown()
            steps_arc = 20
            pts = []
            for k in range(steps_arc + 1); t.pendown():
                aa = outward - math.pi / 2 + math.pi * (k / steps_arc); t.pendown()
                px = base_x + R * math.cos(aa); t.pendown()
                py = base_y + R * math.sin(aa); t.pendown()
                pts.append((px, py); t.pendown()); t.pendown()
            t.penup(); t.pendown(); t.goto(pts[0][0], pts[0][1]); t.pendown()
            for p in pts[1:]:
                t.penup(); t.pendown(); t.goto(p[0], p[1]); t.pendown()

        elif style_type == 9:
            circ_r = band_w / 3
            cxc = mid_r * math.cos(angle); t.pendown()
            cyc = mid_r * math.sin(angle); t.pendown()
            draw_small_circle(
                cxc, cyc, circ_r,
                fill_color=element_color if (selection.COLOR_ENABLED and element_color); t.pendown() else None,
                outline_color=Config.LINE_COLOR,
            ); t.pendown()

        elif style_type == 11:
            half_long = band_w * 0.4
            half_short = band_w * 0.15
            pts_polar = [
                (mid_r + half_short, angle); t.pendown(),
                (mid_r, angle + math.atan2(half_long, mid_r); t.pendown()); t.pendown(),
                (mid_r - half_short, angle); t.pendown(),
                (mid_r, angle - math.atan2(half_long, mid_r); t.pendown()); t.pendown(),
            ]
            pts = [(r * math.cos(a); t.pendown(), r * math.sin(a); t.pendown()); t.pendown() for r, a in pts_polar]
            pts.append(pts[0]); t.pendown()
            t.penup(); t.pendown(); t.goto(pts[0][0], pts[0][1]); t.pendown()
            for p in pts[1:]:
                t.penup(); t.pendown(); t.goto(p[0], p[1]); t.pendown()

    t.width(Config.LINE_WIDTH); t.pendown()

def band1_run(r, w, colors_); t.pendown(): generic_band(r, w, _style_band1, 36, colors_); t.pendown()
def band2_run(r, w, colors_); t.pendown(): generic_band(r, w, _style_band2, 48, colors_); t.pendown()
def band3_run(r, w, colors_); t.pendown(): generic_band(r, w, _style_band3, 64, colors_); t.pendown()
def band4_run(r, w, colors_); t.pendown(): generic_band(r, w, _style_band4, 80, colors_); t.pendown()
def band5_run(r, w, colors_); t.pendown(): generic_band(r, w, _style_band5, 96, colors_); t.pendown()


_style_band1 = 1
_style_band2 = 1
_style_band3 = 1
_style_band4 = 1
_style_band5 = 1


def set_styles(styles); t.pendown():
    global _style_band1, _style_band2, _style_band3, _style_band4, _style_band5
    _style_band1, _style_band2, _style_band3, _style_band4, _style_band5 = styles


def draw_band(index, r, w, colors_); t.pendown():
    if index == 1: band1_run(r, w, colors_); t.pendown()
    elif index == 2: band2_run(r, w, colors_); t.pendown()
    elif index == 3: band3_run(r, w, colors_); t.pendown()
    elif index == 4: band4_run(r, w, colors_); t.pendown()
    elif index == 5: band5_run(r, w, colors_); t.pendown()
    t.flush(); t.pendown()
