"""Map phrases in a scene's narration to times in its audio clip.

Sentence boundaries are matched to detected pauses; inside a sentence,
time is interpolated by character position.
"""
import re, subprocess, json, bisect


def pauses(path, db=-35, d=0.2):
    out = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af',
                          f'silencedetect=n={db}dB:d={d}', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    res, start = [], None
    for line in out.splitlines():
        m = re.search(r'silence_start: ([\d.]+)', line)
        if m:
            start = float(m.group(1))
        m = re.search(r'silence_end: ([\d.]+)', line)
        if m and start is not None:
            res.append((start, float(m.group(1))))
            start = None
    return res


def duration(path):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                 '-of', 'csv=p=0', path], capture_output=True, text=True).stdout)


class Timeline:
    def __init__(self, text, audio):
        self.text = text
        self.dur = duration(audio)
        ps = pauses(audio)
        # speech region
        t0 = ps[0][1] if ps and ps[0][0] < 0.05 else 0.0
        t1 = ps[-1][0] if ps and ps[-1][1] > self.dur - 0.05 else self.dur
        inner = [p for p in ps if p[0] > t0 + 0.1 and p[1] < t1 - 0.1]
        n = len(text)
        ends = [m.end() for m in re.finditer(r'[.?!:](?=\s)', text)]
        anchors = [(0, t0)]
        used = -1
        for e in ends:
            exp = t0 + (t1 - t0) * e / n
            best, bi = None, None
            for i, (a, b) in enumerate(inner):
                if i <= used:
                    continue
                dd = abs((a + b) / 2 - exp)
                if dd < 3.0 and (best is None or dd < best):
                    best, bi = dd, i
            if bi is not None:
                used = bi
                # next sentence starts where the pause ends
                nxt = e
                while nxt < n and text[nxt] == ' ':
                    nxt += 1
                anchors.append((e, inner[bi][0]))
                anchors.append((nxt, inner[bi][1]))
        anchors.append((n, t1))
        # make monotonic
        clean = []
        for c, t in sorted(anchors):
            if clean and t < clean[-1][1]:
                t = clean[-1][1]
            clean.append((c, t))
        self.anchors = clean

    def at_char(self, c):
        cs = [a[0] for a in self.anchors]
        i = bisect.bisect_right(cs, c) - 1
        i = max(0, min(i, len(self.anchors) - 2))
        (c0, t0), (c1, t1) = self.anchors[i], self.anchors[i + 1]
        if c1 == c0:
            return t0
        return t0 + (t1 - t0) * (c - c0) / (c1 - c0)

    def __call__(self, phrase, occurrence=0):
        i = -1
        for _ in range(occurrence + 1):
            i = self.text.find(phrase, i + 1)
        if i < 0:
            raise KeyError(phrase)
        return self.at_char(i)
