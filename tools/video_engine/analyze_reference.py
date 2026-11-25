#!/usr/bin/env python3
"""Frame-by-frame breakdown of a reference motion-graphics video.

Usage:  python3 analyze_reference.py REFERENCE.mp4 [OUT_DIR] [--no-audio]

Writes to OUT_DIR (default ./ref_analysis):
  report.md            numbers to build the style breakdown from (shots, pacing, easing, palette, text, speech)
  shots.csv            every shot: start, end, length, kind (footage-like vs flat graphic), cut type
  motion.csv           per-frame motion energy (how much the picture changes each frame)
  moves.csv            every motion burst: start, length in frames, easing class, peak frame
  palette.json         dominant colours overall and per shot (hex + share)
  keyframes/           first / middle / last frame of every shot (look at these yourself)
  sheets/              contact sheets, one frame every 0.25 s, for frame-by-frame reading
  ocr.json             on-screen text per keyframe (tesseract), to read type hierarchy and wording
  words.json           narration word timings (faster-whisper), if the video has speech

It only measures. Claude reads the numbers AND looks at the keyframes and sheets, then writes the breakdown.
"""
import json, os, subprocess, sys, csv, math
import numpy as np
from PIL import Image, ImageDraw

SMALL = (192, 108)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    out = run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', path]).stdout
    j = json.loads(out)
    v = next(s for s in j['streams'] if s['codec_type'] == 'video')
    num, den = (v.get('avg_frame_rate') or v.get('r_frame_rate')).split('/')
    fps = float(num) / float(den) if float(den) else 30.0
    has_audio = any(s['codec_type'] == 'audio' for s in j['streams'])
    return float(j['format']['duration']), fps, int(v['width']), int(v['height']), has_audio


def frames_small(path, fps):
    """Stream every frame at 192x108 RGB."""
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'scale={SMALL[0]}:{SMALL[1]}', '-f', 'rawvideo',
                          '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    n = SMALL[0] * SMALL[1] * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(SMALL[1], SMALL[0], 3)


def frame_at(path, t, w=None):
    vf = [] if w is None else ['-vf', f'scale={w}:-2']
    out = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', path, '-frames:v', '1'] + vf +
                         ['-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True).stdout
    from io import BytesIO
    return Image.open(BytesIO(out)).convert('RGB')


def kmeans(px, k=8, it=12, seed=1):
    rng = np.random.default_rng(seed)
    c = px[rng.choice(len(px), k, replace=False)].astype(np.float32)
    for _ in range(it):
        d = ((px[:, None, :] - c[None]) ** 2).sum(-1)
        lab = d.argmin(1)
        for i in range(k):
            m = px[lab == i]
            if len(m):
                c[i] = m.mean(0)
    share = np.bincount(lab, minlength=k) / len(lab)
    order = np.argsort(-share)
    return [('#%02X%02X%02X' % tuple(int(v) for v in c[i]), round(float(share[i]), 3)) for i in order]


def classify_ease(curve):
    """curve = per-frame energy of one motion burst. Cumulative progress tells the easing family."""
    cum = np.cumsum(curve)
    if cum[-1] <= 0 or len(curve) < 3:
        return 'cut/instant', 0, 0
    cum = cum / cum[-1]
    n = len(cum)
    t50 = int(np.searchsorted(cum, 0.5)) / max(1, n - 1)
    t90 = int(np.searchsorted(cum, 0.9)) / max(1, n - 1)
    peak = int(np.argmax(curve)) / max(1, n - 1)
    if peak < 0.3 and t50 < 0.35:
        fam = 'ease-out (fast start, long settle: entrance / spring)'
    elif peak > 0.7 and t50 > 0.6:
        fam = 'ease-in (slow start, fast end: exit / whip into a cut)'
    elif 0.3 <= peak <= 0.7 and abs(t50 - 0.5) < 0.12:
        fam = 'ease-in-out (camera move / shared-element morph)'
    else:
        fam = 'linear-ish / continuous (scroll, ticker, drift)'
    return fam, round(t50, 2), round(t90, 2)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'ref_analysis'
    no_audio = '--no-audio' in sys.argv
    for d in ('', 'keyframes', 'sheets'):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    dur, fps, W, H, has_audio = probe(src)

    # ---- per-frame energy + colour samples
    energy, sat, luma, prev, samples = [], [], [], None, []
    for i, f in enumerate(frames_small(src, fps)):
        g = f.astype(np.float32)
        y = 0.2126 * g[..., 0] + 0.7152 * g[..., 1] + 0.0722 * g[..., 2]
        luma.append(float(y.mean()))
        mx, mn = g.max(-1), g.min(-1)
        sat.append(float(((mx - mn) / (mx + 1e-6)).mean()))
        energy.append(0.0 if prev is None else float(np.abs(y - prev).mean()))
        prev = y
        if i % max(1, int(fps / 4)) == 0:
            samples.append((i, f))
    energy = np.array(energy)
    nfr = len(energy)

    # ---- cuts: ffmpeg scene score + energy spikes
    sc = run(['ffmpeg', '-v', 'info', '-i', src, '-vf', "select='gt(scene,0.32)',showinfo", '-f', 'null', '-']).stderr
    cuts = sorted({round(float(l.split('pts_time:')[1].split()[0]), 3) for l in sc.splitlines() if 'pts_time:' in l})
    cut_frames = [int(round(c * fps)) for c in cuts]
    bounds = [0] + cut_frames + [nfr]
    shots = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        if b - a < 2:
            continue
        seg = np.array(sat[a:b])
        tex = float(np.median(energy[a + 1:b])) if b - a > 2 else 0.0
        kind = 'footage-like (texture/noise moves every frame)' if tex > 1.2 else 'flat graphic / held frame'
        pre = energy[max(0, a - 3):a].mean() if a > 3 else 0
        cut_type = 'hard cut' if a == 0 or energy[a] > 3 * max(pre, 0.5) else 'soft (dissolve / morph / blur)'
        shots.append({'start_s': round(a / fps, 3), 'end_s': round(b / fps, 3), 'len_s': round((b - a) / fps, 3),
                      'frames': b - a, 'kind': kind, 'into_shot': cut_type, 'mean_luma': round(float(np.mean(luma[a:b])), 1),
                      'mean_sat': round(float(seg.mean()), 3)})

    # ---- motion bursts (moves) inside shots
    thr = max(0.6, float(np.percentile(energy, 60)))
    moves, i = [], 1
    while i < nfr:
        if energy[i] > thr and i not in cut_frames:
            j = i
            while j < nfr and energy[j] > thr * 0.6 and j not in cut_frames:
                j += 1
            if j - i >= 3:
                fam, t50, t90 = classify_ease(energy[i:j])
                moves.append({'start_s': round(i / fps, 3), 'frames': j - i, 'ms': round(1000 * (j - i) / fps),
                              'peak_s': round((i + int(np.argmax(energy[i:j]))) / fps, 3), 'easing': fam, 't50': t50, 't90': t90})
            i = j
        i += 1

    # ---- keyframes + OCR
    ocr = {}
    have_tess = run(['which', 'tesseract']).returncode == 0
    for k, s in enumerate(shots):
        for tag, t in (('a', s['start_s'] + 0.05), ('m', (s['start_s'] + s['end_s']) / 2), ('z', max(s['start_s'], s['end_s'] - 0.08))):
            im = frame_at(src, t)
            p = os.path.join(out, 'keyframes', f'shot{k + 1:02d}_{tag}_{t:06.2f}.jpg')
            im.save(p, quality=88)
            if have_tess and tag == 'm':
                txt = run(['tesseract', p, '-', '--psm', '11']).stdout
                ocr[os.path.basename(p)] = ' '.join(txt.split())
    # ---- contact sheets (0.25 s steps, 4x4 per sheet)
    step = 0.25
    ts = [round(x * step, 3) for x in range(int(dur / step))]
    for s0 in range(0, len(ts), 16):
        sheet = Image.new('RGB', (4 * 480, 4 * 270), (0, 0, 0))
        dr = ImageDraw.Draw(sheet)
        for q, t in enumerate(ts[s0:s0 + 16]):
            im = frame_at(src, t, 480)
            sheet.paste(im.resize((480, 270)), ((q % 4) * 480, (q // 4) * 270))
            dr.rectangle([(q % 4) * 480, (q // 4) * 270, (q % 4) * 480 + 74, (q // 4) * 270 + 20], fill=(0, 0, 0))
            dr.text(((q % 4) * 480 + 4, (q // 4) * 270 + 4), f'{t:6.2f}s', fill=(255, 80, 80))
        sheet.save(os.path.join(out, 'sheets', f'sheet_{s0 // 16:03d}.jpg'), quality=82)

    # ---- palette
    px = np.concatenate([f.reshape(-1, 3) for _, f in samples]).astype(np.float32)
    px = px[np.random.default_rng(0).choice(len(px), min(60000, len(px)), replace=False)]
    pal = {'overall': kmeans(px, 10)}
    fr_idx = [i for i, _ in samples]
    for k, s in enumerate(shots):
        a, b = int(s['start_s'] * fps), int(s['end_s'] * fps)
        sel = [f.reshape(-1, 3) for i, f in samples if a <= i < b]
        if sel:
            p2 = np.concatenate(sel).astype(np.float32)
            pal[f'shot{k + 1:02d}'] = kmeans(p2[::max(1, len(p2) // 15000)], 5)

    # ---- speech
    words, speech = [], {}
    if has_audio and not no_audio:
        try:
            from faster_whisper import WhisperModel
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
            a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
            m = WhisperModel('small.en', device='cpu', compute_type='int8')
            segs, _ = m.transcribe(a, word_timestamps=True, beam_size=5, condition_on_previous_text=False)
            words = [{'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3)} for sg in segs for w in sg.words]
        except Exception as ex:
            speech['error'] = f'transcription skipped: {ex}'
        if words:
            span = words[-1]['e'] - words[0]['s']
            gaps = [b['s'] - a['e'] for a, b in zip(words, words[1:])]
            near = sum(any(abs(c - w['s']) < 0.25 or abs(c - w['e']) < 0.25 for w in words) for c in cuts)
            sent_end = [w['e'] for w in words if w['w'][-1:] in '.?!']
            on_sentence = sum(any(abs(c - e) < 0.6 for e in sent_end) for c in cuts)
            speech.update({'words': len(words), 'words_per_sec': round(len(words) / max(0.1, span), 2),
                           'pauses_over_0.4s': sum(g > 0.4 for g in gaps),
                           'cuts_within_0.25s_of_a_word_edge': f'{near}/{len(cuts)}',
                           'cuts_within_0.6s_of_a_sentence_end': f'{on_sentence}/{len(cuts)}'})

    # ---- write files
    with open(os.path.join(out, 'shots.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(shots[0].keys())); w.writeheader(); w.writerows(shots)
    with open(os.path.join(out, 'motion.csv'), 'w') as f:
        f.write('frame,time_s,energy,mean_luma,mean_sat\n')
        for i in range(nfr):
            f.write(f'{i},{i / fps:.3f},{energy[i]:.3f},{luma[i]:.1f},{sat[i]:.3f}\n')
    with open(os.path.join(out, 'moves.csv'), 'w', newline='') as f:
        if moves:
            w = csv.DictWriter(f, fieldnames=list(moves[0].keys())); w.writeheader(); w.writerows(moves)
    json.dump(pal, open(os.path.join(out, 'palette.json'), 'w'), indent=1)
    json.dump(ocr, open(os.path.join(out, 'ocr.json'), 'w'), indent=1, ensure_ascii=False)
    json.dump(words, open(os.path.join(out, 'words.json'), 'w'))

    lens = [s['len_s'] for s in shots]
    fams = {}
    for m in moves:
        fams[m['easing']] = fams.get(m['easing'], 0) + 1
    rep = [f'# Reference video measurements: {os.path.basename(src)}', '',
           f'- Duration {dur:.2f} s · {W}x{H} · {fps:.2f} fps · {nfr} frames · audio: {"yes" if has_audio else "no"}',
           f'- Shots: {len(shots)} · length min {min(lens):.2f} s / median {float(np.median(lens)):.2f} s / max {max(lens):.2f} s',
           f'- Cuts per minute: {60 * max(0, len(shots) - 1) / dur:.1f}',
           f'- Footage-like shots: {sum("footage" in s["kind"] for s in shots)} · flat-graphic shots: {sum("flat" in s["kind"] for s in shots)}',
           f'- Hard cuts: {sum(s["into_shot"] == "hard cut" for s in shots)} · soft transitions: {sum(s["into_shot"] != "hard cut" for s in shots)}',
           f'- Motion bursts: {len(moves)} · median length {int(np.median([m["frames"] for m in moves])) if moves else 0} frames',
           '- Easing families: ' + (', '.join(f'{k}: {v}' for k, v in sorted(fams.items(), key=lambda x: -x[1])) or 'none'),
           '- Overall palette (share): ' + ', '.join(f'{h} {int(100 * s)}%' for h, s in pal['overall']),
           f'- Mean saturation {np.mean(sat):.3f} · mean luma {np.mean(luma):.1f}/255', '']
    if speech:
        rep += ['## Speech', ''] + [f'- {k}: {v}' for k, v in speech.items()] + ['']
    rep += ['## Shots', '', '| # | start | len | kind | into shot | luma | sat |', '|---|---|---|---|---|---|---|']
    rep += [f'| {k + 1} | {s["start_s"]:.2f} | {s["len_s"]:.2f} | {s["kind"]} | {s["into_shot"]} | {s["mean_luma"]} | {s["mean_sat"]} |' for k, s in enumerate(shots)]
    rep += ['', '## Moves (first 60)', '', '| start | ms | easing | t50 | t90 |', '|---|---|---|---|---|']
    rep += [f'| {m["start_s"]:.2f} | {m["ms"]} | {m["easing"]} | {m["t50"]} | {m["t90"]} |' for m in moves[:60]]
    rep += ['', 'Next: open keyframes/ and every sheets/ image, read ocr.json, and write the breakdown (see references/reference_video_breakdown.md).']
    open(os.path.join(out, 'report.md'), 'w').write('\n'.join(rep))
    print('\n'.join(rep[:14]))
    print(f'\nWrote {out}/ (report.md, shots.csv, moves.csv, palette.json, keyframes/, sheets/, ocr.json, words.json)')


if __name__ == '__main__':
    main()
