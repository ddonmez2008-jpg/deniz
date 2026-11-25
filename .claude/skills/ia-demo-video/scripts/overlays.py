"""Global overlays: main-section label (top-right) and source document insets."""
import math
import numpy as np
import skia
from lib import W, H, paint, clamp, with_alpha
from design2 import draw_text, text_w, STD
from motion import spring, smooth, lerp, mix_color
from v3style import ACC, TXT, MUTE, GRID, LIGHT, TINT, MR, MT, BG

SECTIONS = ['Introduction', 'Analysis', 'Development', 'Conclusion']
SCENE_SECTION = {'s01': 0, 's02': 0, 's03': 1, 's04': 1, 's05': 1, 's06': 1, 's07': 1, 's07b': 1, 's08': 3,
                 's09': 2, 's10': 2, 's11': 2, 's12': 3}
FIRST_OF = {'s01', 's03', 's08', 's09', 's12'}


def _luma(surf, x, y, w, h):
    info = skia.ImageInfo.Make(w, h, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    surf.readPixels(info, arr, w * 4, x, y)
    a = arr[..., :3].astype(np.float32) / 255.0
    return float((0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]).mean())


def corner_label(c, sid, t, surf=None, luma=None, foot=None):
    """foot = 0..1 how much of the frame is footage (from the shot list); falls back to luminance."""
    k = SCENE_SECTION.get(sid)
    if k is None:
        return
    if foot is not None:
        u = 1 - clamp(foot)
    else:
        L = luma if luma is not None else (_luma(surf, 1500, 40, 324, 70) if surf is not None else 0.9)
        u = clamp((L - 0.42) / 0.2)                   # 1 = light background
    col = mix_color(TINT, ACC, u)
    off = mix_color(LIGHT, GRID, u)
    if sid in FIRST_OF:
        p = spring(t, 0.3, 0.8, 0.9)
    else:
        p = 1.0
    if p <= 0.001:
        return
    if u < 0.99:
        # soft dark corner shade on footage so the light label reads on bright shots
        gp = skia.Paint(AntiAlias=True)
        gp.setShader(skia.GradientShader.MakeRadial((MR - 60, MT + 20), 420,
                     [with_alpha(0xFF0A0C10, 0.55 * (1 - u)), with_alpha(0xFF0A0C10, 0.22 * (1 - u)), with_alpha(0xFF0A0C10, 0.0)],
                     [0.0, 0.45, 1.0]))
        c.drawRect(skia.Rect.MakeLTRB(MR - 60 - 430, 0, W, MT + 20 + 430), gp)
    lab = SECTIONS[k]
    lp = skia.Paint()
    if u < 0.98:
        lp.setImageFilter(skia.ImageFilters.DropShadow(0, 1, 5, 5, with_alpha(0xFF000000, 0.8 * (1 - u))))
    c.saveLayer(None, lp)
    size, tr = 26, 0.0
    tw = text_w(lab, size, 'SemiBold', False, tr)
    x = MR - tw
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x - 20, MT - 4, tw + 40, size * 1.5))
    draw_text(c, lab, x, MT + 2 + (1 - p) * 22, size, 'SemiBold', col, clamp(p * 1.6), display=False, track=tr)
    c.restore()
    # 4-step progress bar under the label
    seg, gap = 24, 6
    total = 4 * seg + 3 * gap
    x0 = MR - total
    for i in range(4):
        q = smooth(clamp((p - 0.2 - i * 0.12) / 0.4))
        cc = col if i == k else off
        a = (1.0 if i == k else lerp(0.32, 0.9, u)) * q
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0 + i * (seg + gap), MT + 42, seg, 3), 2, 2), paint(cc, a))
    c.restore()


# ---------------------------------------------------------------- source document inset
_docs = {}


def _doc(path):
    if path not in _docs:
        _docs[path] = skia.Image.open(path)
    return _docs[path]


def blur_footage(c, S, img, amt, dim=0.45):
    """Defocus the current footage frame (crossfade to a blurred copy) so an inset never fights the subject."""
    if img is None or amt <= 0.002 or not hasattr(S, '_tf'):
        return
    s, fx, fy = S._tf
    p = skia.Paint(AntiAlias=True)
    p.setImageFilter(skia.ImageFilters.Blur(22, 22, skia.TileMode.kClamp))
    p.setAlphaf(clamp(amt))
    c.save(); c.translate(W * fx, H * fy); c.scale(s, s); c.translate(-W * fx, -H * fy)
    c.drawImageRect(img, skia.Rect.MakeWH(W, H), skia.Rect.MakeWH(W, H), skia.SamplingOptions(skia.FilterMode.kLinear), p)
    c.restore()
    c.drawRect(skia.Rect.MakeWH(W, H), paint(0xFF0A0C10, dim * clamp(amt)))


def doc_window(t, t0, dur):
    """0..1 visibility envelope of an inset (for syncing the footage blur)."""
    return smooth(clamp((t - t0 + 0.1) / 0.5)) * (1 - smooth(clamp((t - t0 - dur) / 0.5)))


def doc_inset(c, t, t0, path, caption, dur=4.8, hl=None, stops=(0, 380, 760, 1000), x=1040, y=118, w=784, h=770, light=True, url=None):
    """A real source page slides in on the right, then is scrolled in a few flicks like a reader would.
    hl = highlight box (x0, y0, x1, y1) in page-image pixels, swept in at the start."""
    if t < t0 - 0.05 or t > t0 + dur + 0.6:
        return
    img = _doc(path)
    sc = w / img.width()
    pin = spring(t, t0, 0.8, 0.82)
    pout = smooth(clamp((t - t0 - dur) / 0.45))
    a = clamp(pin * 1.5) * (1 - pout)
    if a <= 0.002:
        return
    dy = (1 - pin) * 80 + pout * 50
    rot = (1 - pin) * -2.5
    # scroll in flicks: hold on the title, then eased steps with short pauses
    # one continuous, gently eased scroll (sine ease-in-out) after a short hold on the title
    s0, s1 = t0 + 1.15, t0 + dur - 0.3
    u = clamp((t - s0) / max(0.1, s1 - s0))
    u = 0.5 - 0.5 * math.cos(math.pi * u)
    off = stops[0] + (stops[-1] - stops[0]) * u
    du = 0.5 * math.pi * math.sin(math.pi * clamp((t - s0) / max(0.1, s1 - s0))) / max(0.1, s1 - s0) if s0 < t < s1 else 0.0
    vel_px_frame = (stops[-1] - stops[0]) * du / 30.0          # on-screen pixels per frame
    c.save()
    c.translate(x + w / 2, y + h / 2 + dy); c.rotate(rot); c.translate(-(x + w / 2), -(y + h / 2))
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), 14, 14)
    sh = skia.Paint(AntiAlias=True)
    sh.setColor(with_alpha(0xFF000000, 0.5 * a))
    sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + 8, y + 22, w, h), 14, 14), sh)
    c.saveLayerAlpha(None, int(255 * a))
    c.clipRRect(rr, doAntiAlias=True)
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint(0xFFFFFFFF))
    c.save()
    bar = 44 if url else 0
    c.translate(x, y + bar - off)
    c.scale(sc, sc)
    ip = skia.Paint(AntiAlias=True)
    if vel_px_frame > 0.6:
        sig = min(3.2, 0.16 * vel_px_frame / sc)                     # light vertical motion blur, page-image pixels
        ip.setImageFilter(skia.ImageFilters.Blur(0.01, sig, skia.TileMode.kClamp))
    c.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), ip)
    if hl:
        g = smooth(clamp((t - t0 - 0.45) / 0.55))
        if g > 0:
            hp = paint(0xFFFFD84D, 0.6)
            hp.setBlendMode(skia.BlendMode.kMultiply)
            c.drawRect(skia.Rect.MakeLTRB(hl[0], hl[1], hl[0] + (hl[2] - hl[0]) * g, hl[3]), hp)
    c.restore()
    fp = skia.Paint(AntiAlias=True)
    fp.setShader(skia.GradientShader.MakeLinear([(x, y + h - 70), (x, y + h)], [with_alpha(0xFFFFFFFF, 0), with_alpha(0xFFFFFFFF, 0.92)]))
    c.drawRect(skia.Rect.MakeXYWH(x, y + h - 70, w, 70), fp)
    if url:
        c.drawRect(skia.Rect.MakeXYWH(x, y, w, bar), paint(0xFFEDEEF0))
        c.drawLine(x, y + bar, x + w, y + bar, paint(0xFFD5D8DD, 1, stroke=1))
        for i, col in enumerate((0xFFEC6A5E, 0xFFF4BF4F, 0xFF61C554)):
            c.drawCircle(x + 22 + i * 18, y + bar / 2, 6, paint(col))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + 90, y + 9, w - 120, bar - 18), 13, 13), paint(0xFFFFFFFF))
        draw_text(c, url, x + 108, y + 13, 17, 'Regular', 0xFF4A4F57, 1, display=False, track=0)
    # thin scroll bar, like a PDF viewer
    total = img.height() * sc
    bh = h * h / total
    by = y + (h - bh) * off / max(1, total - h)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x + w - 10, by + 4, 5, bh - 8), 3, 3), paint(0xFF000000, 0.28))
    c.restore()
    c.restore()
    ca = clamp((t - t0 - 0.2) / 0.4) * (1 - pout)
    draw_text(c, caption.replace(' · ', ': '), x, y - 38 + dy, 24, 'Medium', LIGHT if light else MUTE, ca, display=False, track=0)
