"""IA demo video engine core (premium v6 system: IBM Plex Sans, paper + ink blue, rules not cards)."""
import json, os, subprocess, sys, time, math
import numpy as np
import skia
from lib import W, H, FPS, paint, clamp, with_alpha
from design2 import draw_text, text_w, Grain, EMPH, STD, vignette
from motion import spring, smooth, lerp, mix_color, words_reveal
from cues import Cues
from timing import duration
from v3style import *
from subs import build_chunks, draw_subs
from overlays import corner_label, doc_inset, blur_footage, doc_window

ROOT = os.environ.get('IA_VIDEO_ROOT', os.getcwd())
LEAD, TAIL = 0.35, 0.8
SCRIPT = {s['id']: s['text'] for s in json.load(open(f'{ROOT}/script/scenes.json'))}
ORDER = []  # scene ids in play order, e.g. ['s01', 's02', ...]
PREP = f'{ROOT}/stock/prep'


class Clip:
    def __init__(self, name, start):
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{start:.3f}', '-stream_loop', '-1', '-i', f'{PREP}/{name}.mp4',
                                   '-f', 'rawvideo', '-pix_fmt', 'rgba', '-'], stdout=subprocess.PIPE, bufsize=W * H * 8)
        self.idx, self.img = -1, None

    def get(self, i):
        while self.idx < i:
            buf = self.p.stdout.read(W * H * 4)
            if len(buf) < W * H * 4:
                break
            self.idx += 1
            if self.idx >= i:
                self.img = skia.Image.fromarray(np.frombuffer(buf, np.uint8).reshape(H, W, 4), colorType=skia.kRGBA_8888_ColorType)
        return self.img

    def close(self):
        try:
            self.p.kill()
        except Exception:
            pass


class Shot:
    def __init__(self, t0, fn, clip=None, cstart=0.0, push=(1.0, 1.06), focus=(0.5, 0.45), trans='cut'):
        self.t0, self.fn, self.clip, self.cstart, self.push, self.focus, self.trans = t0, fn, clip, cstart, push, focus, trans
        self.t1 = None
        self.stream = None

    def img(self, t):
        if self.clip is None:
            return None
        if self.stream is None:
            self.stream = Clip(self.clip, self.cstart)
            self.base = self.t0 - 0.4
        return self.stream.get(max(0, int((t - self.base) * FPS)))

    def close(self):
        if self.stream:
            self.stream.close()
            self.stream = None


class Scene:
    def __init__(self, sid):
        self.sid = sid
        self.text = SCRIPT[sid]
        self.cues = Cues(self.text, f'{ROOT}/words/{sid}.json')
        self.L = LEAD + duration(f'{ROOT}/audio/{sid}.mp3') + TAIL
        self.shots = []
        self.blur = []

    def T(self, phrase, occ=0):
        return self.cues(phrase, occ) + LEAD - 0.1

    def add(self, *a, **k):
        s = Shot(*a, **k)
        self.shots.append(s)
        return s


# ---------------------------------------------------------------- generic shot makers
def chapter(num, kick, ls, starts, rule_t, size=124):
    def fn(c, t, S, img):
        c.save()
        s = 1.0 + 0.035 * smooth(t / 6.0)
        c.translate(W * 0.3, H * 0.5); c.scale(s, s); c.translate(-W * 0.3, -H * 0.5)
        y0 = 540 - len(ls) * size * 1.12 / 2
        x = ML
        kk = f'{kick} {int(num)}' if num else kick
        kicker(c, kk, x, y0 - 68, t, LEAD + 0.08)
        yb = lines(c, ls, ML, y0, size, t, starts)
        rule(c, ML, yb + 40, 240, t, rule_t)
        c.restore()
    return fn


def foot(kick, ls, starts, size=78, y=None, big=None, extra=None, source=None, src_t=None, strength=0.78, kick_t=None, dim=0.0, pre=None):
    """Text over full-bleed footage, lower-left."""
    def fn(c, t, S, img):
        if pre:
            pre(c, t, S, img)
        if dim:
            full_scrim(c, dim)
        scrim(c, strength)
        n = len(ls)
        yy = (y if y is not None else 850 - n * size * 1.12)
        if big:
            yy -= big[1] * 1.15
            num_reveal(c, big[0], ML, yy + size * 0 + 10, big[1], t, big[2], LIGHT)
            yy += big[1] * 1.15
        if kick:
            kicker(c, kick, ML, yy - 50, t, starts[0] - 0.1 if kick_t is None else kick_t, TINT)
        lines(c, ls, ML, yy, size, t, starts, LIGHT)
        if extra:
            extra(c, t, S)
        if source:
            src(c, source, t, src_t if src_t is not None else starts[0], light=True)
    return fn


def statement(ls, starts, colors=None, size=116, source=None, sec=None):
    def fn(c, t, S, img):
        c.save()
        s = 1.0 + 0.03 * smooth((t - starts[0]) / 5.0)
        c.translate(W / 2, H / 2); c.scale(s, s); c.translate(-W / 2, -H / 2)
        y0 = 540 - len(ls) * size * 1.16 / 2
        for i, (ln, t0) in enumerate(zip(ls, starts)):
            col = (colors[i] if colors else TXT)
            x = W / 2 - text_w(ln, size) / 2
            words_reveal(c, ln, x, y0 + i * size * 1.16, size, t, t0, col)
        c.restore()
        if sec:
            section(c, sec, t, starts[0])
        if source:
            src(c, source, t, starts[0])
    return fn


def gfx(draw, push=(1.0, 1.03)):
    return draw


# ---------------------------------------------------------------- scenes

# ---- scene builders go here: def build_sNN(S): ... (see VIDEO guide) ----
BUILDERS = {}  # fill: BUILDERS['s01'] = build_s01 ...



# ---------------------------------------------------------------- renderer
def draw_shot(c, S, sh, t, extra=1.0):
    img = sh.img(t)
    if sh.clip is not None:
        c.clear(0xFF000000)
        if img is not None:
            u = smooth(clamp((t - sh.t0) / max(0.5, sh.t1 - sh.t0)))
            s = lerp(sh.push[0], sh.push[1], u) * extra
            fx, fy = sh.focus
            S._tf = (s, fx, fy)
            c.save(); c.translate(W * fx, H * fy); c.scale(s, s); c.translate(-W * fx, -H * fy)
            c.drawImageRect(img, skia.Rect.MakeWH(W, H), skia.Rect.MakeWH(W, H), skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint())
            c.restore()
            vignette(c, 0.4)
        sh.fn(c, t, S, img)
    else:
        c.clear(BG)
        if extra != 1.0:
            c.save(); c.translate(W * 0.4, H * 0.5); c.scale(extra, extra); c.translate(-W * 0.4, -H * 0.5)
        sh.fn(c, t, S, None)
        if extra != 1.0:
            c.restore()


def draw_frame(c, S, t):
    shots = S.shots
    k = 0
    for i, sh in enumerate(shots):
        if t >= sh.t0 - (0.25 if sh.trans == 'zoom' else 0.2 if sh.trans == 'xfade' else 0):
            k = i
    sh = shots[k]
    if k > 0 and sh.trans != 'cut':
        prev = shots[k - 1]
        if sh.trans == 'zoom':
            a0, a1 = sh.t0 - 0.25, sh.t0 + 0.22
        else:
            a0, a1 = sh.t0 - 0.2, sh.t0 + 0.28
        if a0 <= t < a1:
            u = smooth((t - a0) / (a1 - a0))
            draw_shot(c, S, prev, t, extra=(1.0 + 0.45 * u * u) if sh.trans == 'zoom' else 1.0)
            c.saveLayerAlpha(None, int(255 * u))
            draw_shot(c, S, sh, t, extra=(1.0 + 0.10 * (1 - u)) if sh.trans == 'zoom' else 1.0)
            c.restore()
            return
    draw_shot(c, S, sh, t)


def footage_amount(S, t):
    """0..1: how much of the frame at t is stock footage (blends across transitions)."""
    shots = S.shots
    k = 0
    for i, sh in enumerate(shots):
        if t >= sh.t0 - (0.25 if sh.trans == 'zoom' else 0.2 if sh.trans == 'xfade' else 0):
            k = i
    cur = 1.0 if shots[k].clip else 0.0
    if k > 0 and shots[k].trans != 'cut':
        a0, a1 = (shots[k].t0 - 0.25, shots[k].t0 + 0.22) if shots[k].trans == 'zoom' else (shots[k].t0 - 0.2, shots[k].t0 + 0.28)
        if a0 <= t < a1:
            u = smooth((t - a0) / (a1 - a0))
            prev = 1.0 if shots[k - 1].clip else 0.0
            return prev + (cur - prev) * u
    return cur


def in_blur(S, t):
    for sh in S.shots[1:]:
        if sh.trans == 'zoom' and sh.t0 - 0.25 <= t < sh.t0 + 0.22:
            return True
    return False


def make_scene(sid):
    S = Scene(sid)
    BUILDERS[sid](S)
    S.shots.sort(key=lambda s: s.t0)
    for i, sh in enumerate(S.shots):
        sh.t1 = S.shots[i + 1].t0 if i + 1 < len(S.shots) else S.L
    return S


def render(sid, stills=None):
    S = make_scene(sid)
    n = int(round(S.L * FPS))
    os.makedirs(f'{ROOT}/scenes3', exist_ok=True)
    out, tmp = f'{ROOT}/scenes3/{sid}.mp4', f'{ROOT}/scenes3/tmp_{sid}.mp4'
    chunks = build_chunks(S.text, S.cues, LEAD)
    grain = Grain(alpha=0.04)
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    ff = None
    if stills is None:
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS),
                               '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', str(FPS), tmp],
                              stdin=subprocess.PIPE)
        frames = range(n)
    else:
        frames = [int(x * FPS) for x in stills]
    t0w = time.time()
    for i in frames:
        t = i / FPS
        # close finished footage streams
        for sh in S.shots:
            if sh.stream and t > sh.t1 + 0.4:
                sh.close()
        if in_blur(S, t) and stills is None:
            acc = None
            for kk in range(5):
                tt = t - 0.25 / FPS + 0.5 / FPS * (kk + 0.5) / 5
                draw_frame(c, S, tt)
                a = surf.toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32)
                acc = a if acc is None else acc + a
            c.drawImage(skia.Image.fromarray((acc / 5).astype(np.uint8), colorType=skia.kRGBA_8888_ColorType), 0, 0)
        else:
            draw_frame(c, S, t)
        corner_label(c, sid, t, surf, foot=footage_amount(S, t))
        draw_subs(c, chunks, t, surf)
        grain.draw(c, i // 2)
        if sid == ORDER[0] and t < 0.4:
            c.drawRect(skia.Rect.MakeWH(W, H), paint(0xFF000000, 1 - t / 0.4))
        if sid == ORDER[-1] and t > S.L - 0.9:
            c.drawRect(skia.Rect.MakeWH(W, H), paint(0xFF000000, clamp((t - (S.L - 0.9)) / 0.8)))
        if stills is None:
            ff.stdin.write(surf.toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        else:
            surf.makeImageSnapshot().save(f'{ROOT}/stills/v3_{sid}_{t:05.1f}.jpg', skia.kJPEG, 85)
    for sh in S.shots:
        sh.close()
    if ff:
        ff.stdin.close()
        rc = ff.wait()
        if rc == 0:
            os.replace(tmp, out)
        print(sid, n, 'frames', f'{time.time() - t0w:.0f}s', 'rc', rc, flush=True)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        sid = sys.argv[2]
        S = make_scene(sid)
        ts = [ (S.shots[i].t0 + S.shots[i].t1) / 2 + 0.25 * (S.shots[i].t1 - S.shots[i].t0) for i in range(len(S.shots))]
        render(sid, stills=ts)
        print(sid, [round(s.t0, 1) for s in S.shots], round(S.L, 1))
    elif mode == 'render':
        for sid in sys.argv[2:]:
            render(sid)
