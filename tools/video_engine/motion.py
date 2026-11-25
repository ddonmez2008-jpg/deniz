"""Fluid motion helpers: springs, overlapping word reveals, motion-blurred sampling."""
import math
import skia
from lib import font, paint, clamp
from design2 import track_for, text_w, draw_text


def spring(t, t0, dur=0.8, zeta=0.82):
    """Damped spring 0->1 that settles in about `dur` seconds (zeta<1 = tiny overshoot)."""
    if t <= t0:
        return 0.0
    x = t - t0
    w = 4.6 / (zeta * dur)          # settle (2%) ~ dur
    if zeta < 1:
        wd = w * math.sqrt(1 - zeta * zeta)
        return 1 - math.exp(-zeta * w * x) * (math.cos(wd * x) + zeta * w / wd * math.sin(wd * x))
    return 1 - math.exp(-w * x) * (1 + w * x)


def smooth(x):
    x = clamp(x)
    return x * x * x * (x * (6 * x - 15) + 10)   # smootherstep


def lerp(a, b, u):
    return a + (b - a) * u


def mix_color(c1, c2, u):
    u = clamp(u)
    out = 0
    for sh in (24, 16, 8, 0):
        a = (c1 >> sh) & 0xFF
        b = (c2 >> sh) & 0xFF
        out |= int(round(a + (b - a) * u)) << sh
    return out


def words_reveal(c, s, x, y, size, t, t0, color, weight='SemiBold', display=True, stagger=0.065, dur=0.75,
                 rise=None, track=None, caps=False, alpha=1.0):
    """Overlapping action: each word rises on its own spring, staggered; clipped by a line mask."""
    s = s.upper() if caps else s
    words = s.split(' ')
    tr = track_for(size) if track is None else track * size
    space = font(size, weight, display).measureText(' ') + tr
    rise = size * 0.95 if rise is None else rise
    total = text_w(s, size, weight, display, track)
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x - 30, y - size * 0.12, total + 60, size * 1.32))
    xx = x
    for i, w in enumerate(words):
        ww = text_w(w, size, weight, display, track)
        p = spring(t, t0 + i * stagger, dur, 0.86)
        if p > 0.001:
            a = clamp(p * 1.6) * alpha
            draw_text(c, w, xx, y + (1 - p) * rise, size, weight, color, a, display, track)
        xx += ww + space
    c.restore()
    return total


def blur_samples(t, fps, in_window, n=5, shutter=0.5):
    """Sub-frame times for motion blur (180-degree shutter) when in_window(t) is true."""
    if not in_window(t):
        return [t]
    dt = shutter / fps
    return [t - dt / 2 + dt * (k + 0.5) / n for k in range(n)]
