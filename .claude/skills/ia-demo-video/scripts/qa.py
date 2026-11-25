"""Automatic text-collision QA: draws every Nth frame (no encoding), logs every text box,
reports text/text overlaps, text/subtitle overlaps and text outside the frame."""
import sys, json, collections
import skia
import design2
import build  # build.py = engine_core + this video's scene builders
from lib import W, H, FPS
from subs import build_chunks, SUB_Y, SUB_SIZE_PLAIN, font
from design2 import text_w

DUMMY = skia.Image.fromarray(__import__('numpy').zeros((H, W, 4), dtype='uint8'), colorType=skia.kRGBA_8888_ColorType)
build.Shot.img = lambda self, t: (DUMMY if self.clip is not None else None)


def sub_box(chunks, t):
    for ch in chunks:
        if ch['t0'] <= t < ch['t1']:
            s = ' '.join(ch['words'])
            tw = text_w(s, SUB_SIZE_PLAIN, 'Medium', False, 0)
            y = SUB_Y - SUB_SIZE_PLAIN * 0.6
            return (W / 2 - tw / 2 - 10, y + SUB_SIZE_PLAIN * 0.1, W / 2 + tw / 2 + 10, y + SUB_SIZE_PLAIN * 1.2)
    return None


def inter(a, b, pad=2):
    return min(a[2], b[2]) - max(a[0], b[0]) > pad and min(a[3], b[3]) - max(a[1], b[1]) > pad


def in_transition(S, t):
    for sh in S.shots[1:]:
        if sh.trans == 'zoom' and sh.t0 - 0.27 <= t < sh.t0 + 0.24:
            return True
        if sh.trans == 'xfade' and sh.t0 - 0.22 <= t < sh.t0 + 0.30:
            return True
    return False


def qa(sid, stride=2):
    S = build.make_scene(sid)
    chunks = build_chunks(S.text, S.cues, build.LEAD)
    surf = skia.Surface(W, H); c = surf.getCanvas()
    issues = collections.OrderedDict()
    n = int(S.L * FPS)
    for i in range(0, n, stride):
        t = i / FPS
        if in_transition(S, t):
            continue
        design2.TEXT_LOG = []
        build.draw_frame(c, S, t)
        build.corner_label(c, sid, t, None, foot=build.footage_amount(S, t))
        boxes = [b for b in design2.TEXT_LOG if b[4] - b[2] > 6]
        design2.TEXT_LOG = None
        sb = sub_box(chunks, t)
        for j, a in enumerate(boxes):
            if a[4] > 0 and a[2] < H and (a[1] < 40 or a[3] > W - 40):
                issues.setdefault(('EDGE', a[0], ''), []).append(t)
            for b in boxes[j + 1:]:
                if a[0] == b[0] and abs(a[1] - b[1]) < 1:
                    continue
                if a[0] == 'PILL:' + b[0] or b[0] == 'PILL:' + a[0]:
                    continue
                if inter(a[1:5], b[1:5]):
                    issues.setdefault(('TEXT', a[0], b[0]), []).append(t)
            if sb and inter(a[1:5], sb):
                issues.setdefault(('SUB', a[0], ''), []).append(t)
    for sh in S.shots:
        sh.close()
    out = []
    for (kind, s1, s2), ts in issues.items():
        out.append({'kind': kind, 'a': s1, 'b': s2, 't0': round(ts[0], 2), 't1': round(ts[-1], 2), 'n': len(ts)})
    return out


if __name__ == '__main__':
    res = {}
    for sid in sys.argv[1:]:
        r = qa(sid)
        res[sid] = r
        print(f'== {sid}: {len(r)} issue groups', flush=True)
        for x in r[:80]:
            print(f"  {x['kind']:4} {x['t0']:6.2f}-{x['t1']:6.2f} n={x['n']:3}  {x['a'][:40]!r} | {x['b'][:40]!r}")
    json.dump(res, open(f'{build.ROOT}/qa_report.json', 'w'), indent=1)
