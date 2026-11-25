"""v3 style kit: Paper + Ink Blue, fluid motion components."""
import math
import numpy as np
import skia
from lib import W, H, FPS, paint, clamp, with_alpha, font
from design2 import draw_text, text_w, EMPH, STD, vignette
from motion import spring, smooth, lerp, mix_color, words_reveal

# premium system (v6): cooler paper, blue-black ink, deeper ink blue
BG, SURF, TXT, MUTE, GRID = 0xFFEDEBE6, 0xFFE3E1DA, 0xFF1B1F27, 0xFF5A606C, 0xFFCBC8BF
ACC, NEG, BAR = 0xFF1F4F9E, 0xFFB13A2B, 0xFFB9B6AD
LIGHT, TINT, LMUTE = 0xFFF4F3EF, 0xFFB3CBEF, 0xFFD3D7DE
ML, MT, MR = 96, 56, W - 96


# ---------------------------------------------------------------- text blocks
def tidy(s):
    """Sentence-case label text without middle-dot chains."""
    parts = [p.strip() for p in s.split('·')]
    s = ': '.join(parts[:2]) + (', ' + ', '.join(parts[2:]) if len(parts) > 2 else '')
    return s[:1].upper() + s[1:]


def kicker(c, s, x, y, t, t0, color=MUTE, alpha=1.0, size=24):
    """Small label: sentence case, Medium, no tracking (premium system)."""
    return words_reveal(c, tidy(s), x, y - 4, size + 4, t, t0, color, weight='Medium', display=False, track=0, caps=False,
                        stagger=0.03, alpha=alpha)


def lines(c, ls, x, y, size, t, t0s, color=TXT, weight='SemiBold', lh=1.12, alpha=1.0, display=True, align='left'):
    """Multiple lines, each with its own start time. Returns bottom y."""
    if not isinstance(t0s, (list, tuple)):
        t0s = [t0s + i * 0.14 for i in range(len(ls))]
    for i, (s, t0) in enumerate(zip(ls, t0s)):
        xx = x
        if align == 'center':
            xx = x - text_w(s, size, weight, display, None if display else 0) / 2
        words_reveal(c, s, xx, y + i * size * lh, size, t, t0, color, weight=weight, display=display,
                     track=None if display else 0, alpha=alpha)
    return y + len(ls) * size * lh


def body(c, s, x, y, t, t0, color=MUTE, size=36, alpha=1.0):
    return words_reveal(c, s, x, y, size, t, t0, color, weight='Medium', display=False, track=0, alpha=alpha,
                        stagger=0.03)


def src(c, s, t, t0, light=False):
    a = clamp((t - t0) / 0.5)
    if a <= 0:
        return
    many = '·' in s
    body = '; '.join(p.strip() for p in s.split('·'))
    label = ('Sources: ' if many else 'Source: ')
    if body.lower().startswith('source'):          # "Source A: ..." already names itself
        label = ''
    col = 0xFFD9DCE2 if light else MUTE
    draw_text(c, label + body, ML, 996, 24, 'Regular', col, 0.95 * a, display=False, track=0)


def section(c, s, t, t0=0.0):
    a = clamp((t - t0) / 0.5)
    if a > 0:
        draw_text(c, tidy(s), ML, MT + 4, 26, 'Medium', MUTE, a, display=False, track=0)


def rule(c, x, y, w, t, t0, color=ACC, th=4):
    p = spring(t, t0, 0.9, 1.0)
    if p > 0:
        c.drawRect(skia.Rect.MakeXYWH(x, y, w * p, th), paint(color, 1))


# ---------------------------------------------------------------- shapes
def card(c, x, y, w, h, t, t0, fill=None, accent=None, r=16, alpha=1.0, box=False):
    """Quiet tonal panel (premium system): no stripe. accent is ignored except as intent;
    colour now lives in the label text. fill overrides the tone."""
    p = spring(t, t0, 0.7, 0.85)
    if p <= 0.001:
        return 0.0
    a = clamp(p * 1.5) * alpha
    c.save()
    c.translate(0, (1 - p) * 24)
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    c.drawRRect(rr, paint(fill if fill is not None else SURF, a))
    c.restore()
    return a


def pill(c, s, x, y, t, t0, color=ACC, size=28, filled=False):
    p = spring(t, t0, 0.6, 0.8)
    if p <= 0.001:
        return text_w(s, size, 'SemiBold', False, 0) + 52
    w = text_w(s, size, 'SemiBold', False, 0) + 52
    h = size + 30
    a = clamp(p * 1.5)
    import design2 as _d2
    if _d2.TEXT_LOG is not None and a > 0.5:
        r = c.getTotalMatrix().mapRect(skia.Rect.MakeXYWH(x, y, w, h))
        _d2.TEXT_LOG.append(('PILL:' + s, r.left(), r.top(), r.right(), r.bottom(), 0))
    c.save()
    c.translate(x + w / 2, y + h / 2)
    sc = 0.9 + 0.1 * p
    c.scale(sc, sc)
    c.translate(-(x + w / 2), -(y + h / 2))
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), h / 2, h / 2)
    if filled:
        c.drawRRect(rr, paint(color, a))
        draw_text(c, s, x + 26, y + 14, size, 'SemiBold', BG, a, display=False, track=0)
    else:
        c.drawRRect(rr, paint(color, 0.10 * a))
        c.drawRRect(rr, paint(color, a, stroke=2))
        draw_text(c, s, x + 26, y + 14, size, 'SemiBold', color, a, display=False, track=0)
    c.restore()
    return w


def check(c, x, y, s, t, t0, color=ACC, w=6):
    p = smooth(clamp((t - t0) / 0.45))
    if p <= 0:
        return
    path = skia.Path()
    path.moveTo(x, y + s * 0.5); path.lineTo(x + s * 0.38, y + s * 0.88); path.lineTo(x + s, y + s * 0.1)
    meas = skia.PathMeasure(path, False)
    seg = skia.Path()
    meas.getSegment(0, meas.getLength() * p, seg, True)
    c.drawPath(seg, paint(color, 1, stroke=w))


def cross(c, x, y, s, t, t0, color=NEG, w=6):
    p1 = smooth(clamp((t - t0) / 0.25))
    p2 = smooth(clamp((t - t0 - 0.15) / 0.25))
    if p1 > 0:
        c.drawLine(x, y, x + s * p1, y + s * p1, paint(color, 1, stroke=w))
    if p2 > 0:
        c.drawLine(x + s, y, x + s - s * p2, y + s * p2, paint(color, 1, stroke=w))


def person(c, x, y, s, color, a=1.0, scale=1.0):
    if a <= 0.001 or scale <= 0.001:
        return
    s = s * scale
    c.drawCircle(x, y - s * 0.55, s * 0.28, paint(color, a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - s * 0.42, y - s * 0.18, s * 0.84, s * 0.62), s * 0.3, s * 0.3), paint(color, a))


def hbar(c, x, y, w, h, frac, color, a=1.0, r=8):
    if frac <= 0.001 or a <= 0:
        return
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, max(h * 0.2, w * frac), h), r, r), paint(color, a))


def ring(c, x, y, r, frac, color, a=1.0, w=30):
    if a <= 0:
        return
    c.drawCircle(x, y, r, paint(GRID, a, stroke=w))
    if frac > 0:
        p = paint(color, a, stroke=w)
        c.drawArc(skia.Rect.MakeXYWH(x - r, y - r, 2 * r, 2 * r), -90, 360 * frac, False, p)


def arrow(c, x0, y0, x1, y1, t, t0, color=MUTE, w=3, head=12, d=0.6):
    p = EMPH(clamp((t - t0) / d))
    if p <= 0:
        return
    xe, ye = lerp(x0, x1, p), lerp(y0, y1, p)
    c.drawLine(x0, y0, xe, ye, paint(color, 1, stroke=w))
    ang = math.atan2(y1 - y0, x1 - x0)
    path = skia.Path()
    path.moveTo(xe, ye)
    path.lineTo(xe - head * math.cos(ang - 0.45), ye - head * math.sin(ang - 0.45))
    path.lineTo(xe - head * math.cos(ang + 0.45), ye - head * math.sin(ang + 0.45))
    path.close()
    c.drawPath(path, paint(color, 1))


def counter(v0, v1, t, t0, d=1.1):
    return lerp(v0, v1, EMPH(clamp((t - t0) / d)))


def num_reveal(c, s, x, y, size, t, t0, color=ACC, align='left'):
    """Big number with a rise + fade (used when the digits change)."""
    p = spring(t, t0, 0.7, 0.86)
    if p <= 0.001:
        return
    xx = x - text_w(s, size) if align == 'right' else x
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(xx - 30, y - size * 0.12, text_w(s, size) + 60, size * 1.32))
    draw_text(c, s, xx, y + (1 - p) * size * 0.9, size, 'SemiBold', color, clamp(p * 1.6))
    c.restore()


# ---------------------------------------------------------------- footage overlay
def scrim(c, strength=0.78):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([(0, H), (W * 0.62, H * 0.28)],
                                               [with_alpha(0xFF0A0C10, strength), with_alpha(0xFF0A0C10, strength * 0.55),
                                                with_alpha(0xFF0A0C10, 0.0)], [0.0, 0.35, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def full_scrim(c, a=0.45):
    c.drawRect(skia.Rect.MakeWH(W, H), paint(0xFF0A0C10, a))


def colrule(c, x, y, w, h, t, t0, fill=None, accent=None, r=16, alpha=1.0, box=False):
    """Premium column marker instead of a panel: a hairline with the accent drawn over it.
    Same signature as card(); h/fill/r are ignored. Returns the reveal progress."""
    p = spring(t, t0, 0.8, 1.0)
    if p <= 0.001:
        return 0.0
    a = clamp(p * 1.6) * alpha
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, 1.5), paint(GRID, a))
    c.drawRect(skia.Rect.MakeXYWH(x, y - 1, w * EMPH(clamp(p)) * 0.22, 4), paint(accent or ACC, a))
    return a
