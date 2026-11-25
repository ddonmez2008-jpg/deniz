"""Word-timed subtitles in the house style (Ink pill, Inter Medium, current word tinted)."""
import re
import skia
from lib import W, H, paint, clamp, font
from design2 import draw_text, text_w
from motion import spring

SUB_Y = 948            # vertical centre of the subtitle pill
SUB_SIZE = 36
SUB_MAXCH = 44         # max characters per chunk (one line)
PILL = 0xFF16181D
TXT = 0xFFF5F3EE
CUR = 0xFFA9C8F2


def build_chunks(text, cues, lead):
    """Split the narration into one-line chunks with word start times (scene time)."""
    words = [(m.group(), m.start()) for m in re.finditer(r'\S+', text)]
    times = []
    for w, ch in words:
        t = None
        for k, (_, c) in enumerate(cues.st):
            if c >= ch:
                t = cues.times[k]
                break
        times.append((t if t is not None else cues.times[-1]) + lead)
    # show numbers as digits so subtitles match the graphics
    U = {'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,
         'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18,'nineteen':19}
    TENS = {'twenty':20,'thirty':30,'forty':40,'fifty':50,'sixty':60,'seventy':70,'eighty':80,'ninety':90}
    NUM = r"(?:(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)(?:-(?:one|two|three|four|five|six|seven|eight|nine))?|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|one|two|three|four|five|six|seven|eight|nine|ten)"
    def val(w):
        w = w.lower()
        if '-' in w:
            a_, b_ = w.split('-'); return TENS[a_] + U[b_]
        return TENS.get(w, U.get(w))
    reps = [
        (r"two point eight percent", '2.8%'),
        (r"one hundred and seventy-five", '175'),
        (r"three-hundred", '300'),
        (r"six and a half points", '6.5 points'),
        (r"(" + NUM + r") thousand", lambda m: f"{val(m.group(1)) * 1000:,}"),
        (r"(" + NUM + r") to (" + NUM + r") percent", lambda m: f"{val(m.group(1))}–{val(m.group(2))}%"),
        (r"(" + NUM + r") percentage points", lambda m: f"{val(m.group(1))} percentage points"),
        (r"(" + NUM + r") percent", lambda m: f"{val(m.group(1))}%"),
        (r"\b(fifty) employees", lambda m: '50 employees'),
    ]
    spans = []
    for pat, rep in reps:
        for m in re.finditer(pat, text, re.I):
            if any(m.start() < e and m.end() > s for s, e, _ in spans):
                continue
            spans.append((m.start(), m.end(), rep(m) if callable(rep) else rep))
    if spans:
        nw, nt = [], []
        i = 0
        while i < len(words):
            w, ch = words[i]
            sp = next((x for x in spans if x[0] <= ch < x[1]), None)
            if sp is None:
                nw.append((w, ch)); nt.append(times[i]); i += 1; continue
            j = i
            while j + 1 < len(words) and words[j + 1][1] < sp[1]:
                j += 1
            tail = re.sub(r'^.*?([.,;:?!]*)$', r'\1', words[j][0])
            nw.append((sp[2] + tail, ch)); nt.append(times[i])
            i = j + 1
        words, times = nw, nt
    # 1) clauses at punctuation  2) merge short clauses  3) split long ones evenly
    clauses, cur = [], []
    for i, (w, _) in enumerate(words):
        cur.append(i)
        if re.search(r'[.?!:;]$', w) or (re.search(r',$', w) and len(cur) >= 3):
            clauses.append(cur); cur = []
    if cur:
        clauses.append(cur)
    L = lambda idx: sum(len(words[k][0]) for k in idx) + len(idx) - 1
    merged = []
    for cl in clauses:
        if merged and (L(cl) < 16 or L(merged[-1]) < 16) and L(merged[-1]) + 1 + L(cl) <= SUB_MAXCH \
                and not re.search(r'[.?!]$', words[merged[-1][-1]][0]):
            merged[-1] = merged[-1] + cl
        else:
            merged.append(cl)
    chunks = []
    for cl in merged:
        n = -(-L(cl) // SUB_MAXCH)
        if n <= 1:
            chunks.append(cl); continue
        target = L(cl) / n
        part, acc = [], 0
        for k in cl:
            add = len(words[k][0]) + (1 if part else 0)
            if part and acc + add / 2 > target * (len(chunks) and 1) and acc >= target * 0.8 and len(cl) - cl.index(k) >= 2:
                chunks.append(part); part, acc = [], 0; add = len(words[k][0])
            part.append(k); acc += add
        chunks.append(part)
    out = []
    for ci, idxs in enumerate(chunks):
        t0 = times[idxs[0]] - 0.08
        last = idxs[-1]
        t_last_end = times[last + 1] if last + 1 < len(times) else times[last] + 0.6
        nxt = times[chunks[ci + 1][0]] - 0.08 if ci + 1 < len(chunks) else t_last_end + 0.5
        t1 = min(nxt, t_last_end + 0.6)
        out.append({'t0': t0, 't1': t1, 'words': [words[i][0] for i in idxs], 'wt': [times[i] for i in idxs]})
    return out


def _band_luma(surf):
    """Mean luminance (0-1) of the band behind the subtitles."""
    import numpy as np
    info = skia.ImageInfo.Make(960, 70, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    arr = np.zeros((70, 960, 4), dtype=np.uint8)
    surf.readPixels(info, arr, 960 * 4, 480, SUB_Y - 35)
    a = arr[..., :3].astype(np.float32) / 255.0
    return float((0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]).mean())


def _mix(c1, c2, u):
    out = 0xFF000000
    for sh in (16, 8, 0):
        a, b = (c1 >> sh) & 255, (c2 >> sh) & 255
        out |= int(round(a + (b - a) * u)) << sh
    return out


INK, ACC = 0xFF16181D, 0xFF1F5AA6
SUB_SIZE_PLAIN = 38


def draw_subs(c, chunks, t, surf=None, luma=None):
    """Plain subtitles: light text + soft shadow on footage, ink text on paper."""
    for ch in chunks:
        if ch['t0'] <= t < ch['t1'] + 0.12:
            p = spring(t, ch['t0'], 0.35, 0.9)
            out = clamp((t - ch['t1']) / 0.12)
            a = clamp(p * 1.6) * (1 - out)
            if a <= 0.01:
                return
            L = luma if luma is not None else (_band_luma(surf) if surf is not None else 0.2)
            u = clamp((L - 0.45) / 0.2)          # 0 = dark footage, 1 = paper
            base = _mix(TXT, INK, u)
            cur = _mix(CUR, ACC, u)
            size = SUB_SIZE_PLAIN
            f = font(size, 'Medium', False)
            sp = f.measureText(' ')
            ws = [text_w(w, size, 'Medium', False, 0) for w in ch['words']]
            tw = sum(ws) + sp * (len(ws) - 1)
            x = W / 2 - tw / 2
            y = SUB_Y - size * 0.6 + (1 - p) * 8
            shadow_a = 0.75 * (1 - u)
            lp = skia.Paint()
            if shadow_a > 0.02:
                lp.setImageFilter(skia.ImageFilters.DropShadow(0, 2, 6, 6, skia.Color4f(0, 0, 0, shadow_a).toColor()))
            c.saveLayer(None, lp)
            xx = x
            for i, wd in enumerate(ch['words']):
                spoken = t >= ch['wt'][i]
                nxt = ch['wt'][i + 1] if i + 1 < len(ch['wt']) else ch['t1']
                current = spoken and t < nxt
                draw_text(c, wd, xx, y, size, 'Medium', cur if current else base,
                          a * (1.0 if spoken else 0.72), display=False, track=0)
                xx += ws[i] + sp
            c.restore()
            return
