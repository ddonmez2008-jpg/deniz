import math, os, subprocess
import numpy as np
import skia

W, H, FPS = 1920, 1080, 30
FONT_DIR = os.environ.get('IA_VIDEO_FONT_DIR', '/usr/share/fonts/opentype/inter/')

# palette
BG = 0xFF0D1626
BG2 = 0xFF15223A
PANEL = 0xFF1A2944
LINE = 0xFF2B3D5E
WHITE = 0xFFF5F7FA
MUTED = 0xFF9AA8BF
TEAL = 0xFF2EC4B6
AMBER = 0xFFFFB703
CORAL = 0xFFEF476F
BLUE = 0xFF4EA8DE
GREEN = 0xFF7BD389

_tf = {}


def tf(weight='Regular', display=False):
    key = (weight, display)
    if key not in _tf:
        name = ('InterDisplay-' if display else 'Inter-') + weight + '.otf'
        _tf[key] = skia.Typeface.MakeFromFile(FONT_DIR + name)
    return _tf[key]


_fonts = {}


def font(size, weight='Regular', display=False):
    key = (size, weight, display)
    if key not in _fonts:
        f = skia.Font(tf(weight, display), size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setSubpixel(True)
        _fonts[key] = f
    return _fonts[key]


def with_alpha(color, a):
    a = max(0.0, min(1.0, a))
    base = (color >> 24) & 0xFF
    return (int(base * a) << 24) | (color & 0xFFFFFF)


def paint(color, a=1.0, stroke=0, aa=True):
    p = skia.Paint(AntiAlias=aa, Color=with_alpha(color, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


# ---------- easing / timing ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def prog(t, t0, d=0.6):
    return ease_out((t - t0) / d) if d > 0 else (1.0 if t >= t0 else 0.0)


def window(t, t_in, t_out=None, d_in=0.5, d_out=0.4):
    """Visibility 0..1 for an element shown from t_in until t_out."""
    v = prog(t, t_in, d_in)
    if t_out is not None:
        v *= 1 - ease_in_out((t - t_out) / d_out)
    return clamp(v)


# ---------- drawing ----------
def text_width(s, size, weight='Regular', display=False):
    return font(size, weight, display).measureText(s)


def wrap(s, size, maxw, weight='Regular', display=False):
    f = font(size, weight, display)
    words, lines, cur = s.split(' '), [], ''
    for w in words:
        test = (cur + ' ' + w).strip()
        if f.measureText(test) <= maxw or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text(c, s, x, y, size=36, weight='Regular', color=WHITE, a=1.0, align='left',
         maxw=None, lh=1.25, display=False):
    """Draw text with top-left at (x, y) (baseline computed). Returns height used."""
    if a <= 0.001:
        lines = wrap(s, size, maxw, weight, display) if maxw else [s]
        return len(lines) * size * lh
    f = font(size, weight, display)
    lines = wrap(s, size, maxw, weight, display) if maxw else [s]
    p = paint(color, a)
    for i, ln in enumerate(lines):
        w = f.measureText(ln)
        xx = x - w / 2 if align == 'center' else (x - w if align == 'right' else x)
        c.drawString(ln, xx, y + size * 0.95 + i * size * lh, f, p)
    return len(lines) * size * lh


def rrect(c, x, y, w, h, r=18, color=PANEL, a=1.0, stroke=0, scolor=None):
    rect = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    if color is not None:
        c.drawRRect(rect, paint(color, a))
    if stroke:
        c.drawRRect(rect, paint(scolor or LINE, a, stroke=stroke))


def circle(c, x, y, r, color, a=1.0, stroke=0):
    c.drawCircle(x, y, r, paint(color, a, stroke=stroke))


def line(c, x0, y0, x1, y1, color=LINE, a=1.0, w=3):
    c.drawLine(x0, y0, x1, y1, paint(color, a, stroke=w))


def arrow(c, x0, y0, x1, y1, color=MUTED, a=1.0, w=4, p=1.0, head=16):
    if p <= 0 or a <= 0:
        return
    xe, ye = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    line(c, x0, y0, xe, ye, color, a, w)
    ang = math.atan2(y1 - y0, x1 - x0)
    path = skia.Path()
    path.moveTo(xe, ye)
    path.lineTo(xe - head * math.cos(ang - 0.45), ye - head * math.sin(ang - 0.45))
    path.lineTo(xe - head * math.cos(ang + 0.45), ye - head * math.sin(ang + 0.45))
    path.close()
    c.drawPath(path, paint(color, a))


def check(c, x, y, s, color, a=1.0, w=6, p=1.0):
    path = skia.Path()
    pts = [(x, y + s * 0.5), (x + s * 0.38, y + s * 0.88), (x + s, y + s * 0.1)]
    path.moveTo(*pts[0])
    path.lineTo(*pts[1])
    path.lineTo(*pts[2])
    meas = skia.PathMeasure(path, False)
    seg = skia.Path()
    meas.getSegment(0, meas.getLength() * clamp(p), seg, True)
    c.drawPath(seg, paint(color, a, stroke=w))


def cross(c, x, y, s, color, a=1.0, w=6):
    line(c, x, y, x + s, y + s, color, a, w)
    line(c, x + s, y, x, y + s, color, a, w)


def person(c, x, y, s, color, a=1.0):
    circle(c, x, y - s * 0.55, s * 0.28, color, a)
    rect = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - s * 0.42, y - s * 0.18, s * 0.84, s * 0.62), s * 0.3, s * 0.3)
    c.drawRRect(rect, paint(color, a))


def push(c, a=1.0, dy=0.0, dx=0.0, scale=1.0, cx=0, cy=0):
    """Save layer with alpha and offset. Pair with c.restore()."""
    if a < 0.999:
        c.saveLayerAlpha(None, int(255 * clamp(a)))
    else:
        c.save()
    c.translate(dx, dy)
    if scale != 1.0:
        c.translate(cx, cy)
        c.scale(scale, scale)
        c.translate(-cx, -cy)


def chip(c, s, x, y, color=TEAL, a=1.0, size=24):
    w = text_width(s, size, 'SemiBold') + 44
    rrect(c, x, y, w, size + 22, (size + 22) / 2, color=color, a=0.16 * a)
    rrect(c, x, y, w, size + 22, (size + 22) / 2, color=None, a=a, stroke=2, scolor=color)
    text(c, s, x + 22, y + 10, size, 'SemiBold', color, a)
    return w


def counter_text(v, fmt='{:.0f}'):
    return fmt.format(v)


# ---------- b-roll ----------
class BRoll:
    """Streams frames from a pre-made 1920x1080 30fps loop file."""

    def __init__(self, path):
        self.proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-stream_loop', '-1', '-i', path,
                                      '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
                                     stdout=subprocess.PIPE, bufsize=W * H * 4 * 2)
        self.img = None

    def next(self):
        buf = self.proc.stdout.read(W * H * 4)
        if len(buf) == W * H * 4:
            arr = np.frombuffer(buf, np.uint8).reshape(H, W, 4)
            self.img = skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)
        return self.img

    def close(self):
        self.proc.kill()


def draw_image_cover(c, img, x, y, w, h, a=1.0, r=0, fx=0.5, fy=0.5):
    if img is None:
        return
    iw, ih = img.width(), img.height()
    s = max(w / iw, h / ih)
    sw, sh = w / s, h / s
    src = skia.Rect.MakeXYWH((iw - sw) * fx, (ih - sh) * fy, sw, sh)
    c.save()
    if r:
        c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), doAntiAlias=True)
    p = skia.Paint(AntiAlias=True)
    p.setAlphaf(clamp(a))
    c.drawImageRect(img, src, skia.Rect.MakeXYWH(x, y, w, h), skia.SamplingOptions(skia.FilterMode.kLinear), p)
    c.restore()


def vgrad(c, x, y, w, h, c0, a0, c1, a1):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([(x, y), (x, y + h)], [with_alpha(c0, a0), with_alpha(c1, a1)]))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), p)


def hgrad(c, x, y, w, h, c0, a0, c1, a1):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([(x, y), (x + w, y)], [with_alpha(c0, a0), with_alpha(c1, a1)]))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), p)


def background(c, t):
    c.clear(BG)
    # slow drifting glow for life
    p = skia.Paint(AntiAlias=True)
    gx = W * 0.75 + math.sin(t * 0.15) * 120
    gy = H * 0.25 + math.cos(t * 0.11) * 80
    p.setShader(skia.GradientShader.MakeRadial((gx, gy), 900, [with_alpha(0xFF1E3A5F, 0.55), with_alpha(BG, 0.0)]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    # faint grid dots
    dp = paint(0xFF22324F, 0.5)
    for yy in range(60, H, 60):
        for xx in range(60, W, 60):
            c.drawCircle(xx, yy, 1.4, dp)
