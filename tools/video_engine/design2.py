"""v2 design system: Ink palette, Inter Display, mask-reveal type, graded footage, grain."""
import math, subprocess
import numpy as np
import skia
from lib import tf, font, with_alpha, paint, clamp, W, H, FPS

# ---- Ink palette (research: one accent + one contrast, neutrals, no glow)
INK = 0xFF0F1216
SURF = 0xFF1A1F26
GRID = 0xFF2B323B
TXT = 0xFFF3F1EC
MUTE = 0xFF9AA3AE
AMB = 0xFFF5B83D
BLU = 0xFF6FA8FF
ML, MT = 96, 54          # title-safe margins


# ---- easing: cubic-bezier solver
def bezier(p1x, p1y, p2x, p2y):
    def f(x):
        x = clamp(x)
        lo, hi = 0.0, 1.0
        for _ in range(28):
            t = (lo + hi) / 2
            bx = 3 * (1 - t) ** 2 * t * p1x + 3 * (1 - t) * t * t * p2x + t ** 3
            if bx < x:
                lo = t
            else:
                hi = t
        t = (lo + hi) / 2
        return 3 * (1 - t) ** 2 * t * p1y + 3 * (1 - t) * t * t * p2y + t ** 3
    return f


EMPH = bezier(0.05, 0.7, 0.1, 1.0)     # entrances
STD = bezier(0.2, 0.0, 0.0, 1.0)       # moves
EXIT = bezier(0.3, 0.0, 0.8, 0.15)     # exits


def p_in(t, t0, d=0.7):
    return EMPH((t - t0) / d) if t >= t0 else 0.0


def p_out(t, t0, d=0.4):
    return EXIT((t - t0) / d) if t >= t0 else 0.0


# ---- text with tracking
def track_for(size):
    return (-0.0223 + 0.185 * math.exp(-0.1745 * size)) * size


TEXT_LOG = None
TEXT_LOG_GROUP = []


def draw_text(c, s, x, y, size, weight='SemiBold', color=TXT, a=1.0, display=True, track=None, align='left', caps=False):
    """Top-left anchored, per-glyph tracking. Returns width."""
    f = font(size, weight, display)
    if caps:
        s = s.upper()
    tr = track_for(size) if track is None else track * size
    widths = [f.measureText(ch) for ch in s]
    total = sum(widths) + tr * (len(s) - 1)
    if align == 'center':
        x -= total / 2
    elif align == 'right':
        x -= total
    if a > 0.001:
        p = paint(color, a)
        base = y + size * 0.93
        if TEXT_LOG is not None and a > 0.5 and s.strip():
            r = c.getTotalMatrix().mapRect(skia.Rect.MakeLTRB(x, y + size * 0.18, x + total, y + size * 1.12))
            TEXT_LOG.append((s, r.left(), r.top(), r.right(), r.bottom(), id(TEXT_LOG_GROUP[0]) if TEXT_LOG_GROUP else 0))
        if abs(tr) < 0.01:
            c.drawString(s, x, base, f, p)
        else:
            xx = x
            blob = skia.TextBlob.MakeFromPosTextH(s, [x + sum(widths[:i]) + tr * i for i in range(len(s))], base, f) if hasattr(skia.TextBlob, 'MakeFromPosTextH') else None
            if blob is not None:
                c.drawTextBlob(blob, 0, 0, p)
            else:
                for i, ch in enumerate(s):
                    c.drawString(ch, xx, base, f, p)
                    xx += widths[i] + tr
    return total


def text_w(s, size, weight='SemiBold', display=True, track=None):
    f = font(size, weight, display)
    tr = track_for(size) if track is None else track * size
    return sum(f.measureText(ch) for ch in s) + tr * (len(s) - 1)


def reveal_line(c, s, x, y, size, t, t0, weight='SemiBold', color=TXT, display=True, d=0.75, rise=None, align='left',
                caps=False, track=None, t_out=None):
    """Mask reveal: line rises from behind a clip rect. Returns width."""
    p = p_in(t, t0, d)
    if t_out is not None:
        q = p_out(t, t_out, 0.4)
    else:
        q = 0
    if p <= 0:
        return text_w(s.upper() if caps else s, size, weight, display, track)
    rise = size * 0.9 if rise is None else rise
    w = text_w(s.upper() if caps else s, size, weight, display, track)
    xx = x - w / 2 if align == 'center' else (x - w if align == 'right' else x)
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(xx - 20, y - 4, w + 40, size * 1.25))
    dy = (1 - p) * rise - q * rise
    draw_text(c, s, xx, y + dy, size, weight, color, min(1, p * 1.4) * (1 - q), display, track, caps=caps)
    c.restore()
    return w


# ---- camera
def push(c, t, t0, t1, s0=1.0, s1=1.06, cx=W / 2, cy=H / 2):
    u = clamp((t - t0) / max(0.01, t1 - t0))
    u = 0.5 - 0.5 * math.cos(math.pi * u)
    s = s0 + (s1 - s0) * u
    c.translate(cx, cy)
    c.scale(s, s)
    c.translate(-cx, -cy)


# ---- footage: graded stream
GRADE = "eq=saturation=0.80:contrast=1.05:brightness=-0.015:gamma=0.98,colorbalance=rs=0.02:bs=-0.03:rm=0.015:bm=-0.02"


class Footage:
    def __init__(self, path, start=0.0, speed=1.0, hflip=False):
        vf = f"{GRADE}" + (",hflip" if hflip else "") + (f",setpts={1/speed}*PTS,fps=30" if speed != 1.0 else "")
        self.proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{start}', '-stream_loop', '-1', '-i', path,
                                      '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'],
                                     stdout=subprocess.PIPE, bufsize=W * H * 4 * 2)
        self.img = None

    def next(self):
        buf = self.proc.stdout.read(W * H * 4)
        if len(buf) == W * H * 4:
            self.img = skia.Image.fromarray(np.frombuffer(buf, np.uint8).reshape(H, W, 4), colorType=skia.kRGBA_8888_ColorType)
        return self.img

    def close(self):
        self.proc.kill()


def full_bleed(c, img, t, t0, t1, s0=1.0, s1=1.05, fx=0.5, fy=0.5):
    if img is None:
        return
    c.save()
    push(c, t, t0, t1, s0, s1, W * fx, H * fy)
    c.drawImageRect(img, skia.Rect.MakeWH(img.width(), img.height()), skia.Rect.MakeWH(W, H),
                    skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint())
    c.restore()


def vignette(c, strength=0.45):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial((W / 2, H / 2), W * 0.75,
                                               [with_alpha(0xFF000000, 0.0), with_alpha(0xFF000000, 0.0), with_alpha(0xFF000000, strength)],
                                               [0.0, 0.55, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


def scrim_bottom_left(c, a=0.6):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([(0, H), (W * 0.7, H * 0.35)],
                                               [with_alpha(0xFF000000, a), with_alpha(0xFF000000, a * 0.55), with_alpha(0xFF000000, 0.0)],
                                               [0.0, 0.3, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)


# ---- grain (applied once, over everything)
class Grain:
    def __init__(self, n=6, alpha=0.055, seed=7):
        rng = np.random.default_rng(seed)
        self.imgs = []
        for _ in range(n):
            g = rng.normal(0.5, 0.18, (H // 2, W // 2)).clip(0, 1)
            v = (g * 255).astype(np.uint8)
            arr = np.dstack([v, v, v, np.full_like(v, int(255 * alpha))])
            # premultiply
            pm = (arr[..., :3].astype(np.uint16) * arr[..., 3:4] // 255).astype(np.uint8)
            arr = np.dstack([pm, arr[..., 3]])
            self.imgs.append(skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType,
                                                  alphaType=skia.kPremul_AlphaType))
        self.paint = skia.Paint()
        self.paint.setBlendMode(skia.BlendMode.kOverlay)

    def draw(self, c, frame):
        img = self.imgs[frame % len(self.imgs)]
        c.drawImageRect(img, skia.Rect.MakeWH(img.width(), img.height()), skia.Rect.MakeWH(W, H),
                        skia.SamplingOptions(skia.FilterMode.kLinear), self.paint)


# ---- source line (bottom-left, muted)
def source_line(c, s, a):
    if a <= 0.001:
        return
    draw_text(c, 'SOURCE', ML, 1026 - 24, 18, 'Medium', MUTE, 0.8 * a, display=False, track=0.08)
    draw_text(c, s, ML + text_w('SOURCE', 18, 'Medium', False, 0.08) + 14, 1026 - 27, 22, 'Regular', MUTE, 0.9 * a, display=False, track=0.0)


def rule(c, x, y, w, color, a, p, th=3):
    if p <= 0 or a <= 0:
        return
    c.drawRect(skia.Rect.MakeXYWH(x, y, w * p, th), paint(color, a))
