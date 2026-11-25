"""Phrase -> audio time, using whisper word timestamps aligned to the script text."""
import json, re, difflib

ONES = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS = 'zero ten twenty thirty forty fifty sixty seventy eighty ninety'.split()


def n2w(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ('' if n % 10 == 0 else ' ' + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + ' hundred' + ('' if n % 100 == 0 else ' and ' + n2w(n % 100))
    return n2w(n // 1000) + ' thousand' + ('' if n % 1000 == 0 else ' ' + n2w(n % 1000))


def norm_word(w):
    w = w.lower().replace('-', ' ')
    out = []
    for tok in re.findall(r"[a-z']+|\d+(?:\.\d+)?|%|,000", w):
        if tok == '%':
            out.append('percent')
        elif tok == ',000':
            out.append('thousand')
        elif re.fullmatch(r'\d+\.\d+', tok):
            a, b = tok.split('.')
            out += n2w(int(a)).split() + ['point'] + [ONES[int(ch)] for ch in b]
        elif tok.isdigit():
            out += n2w(int(tok)).split()
        else:
            out.append(tok.strip("'"))
    return [o for o in out if o]


class Cues:
    def __init__(self, text, words_path):
        self.text = text
        words = json.load(open(words_path))
        # script tokens with char offsets
        self.st = []
        for m in re.finditer(r"[A-Za-z0-9'\-]+", text):
            for sub in norm_word(m.group()):
                self.st.append((sub, m.start()))
        wt = []
        for w in words:
            subs = norm_word(w['w'])
            for k, sub in enumerate(subs):
                frac = k / max(1, len(subs))
                wt.append((sub, w['s'] + (w['e'] - w['s']) * frac))
        a = [s for s, _ in self.st]
        b = [s for s, _ in wt]
        times = [None] * len(a)
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                times[blk.a + k] = wt[blk.b + k][1]
        # interpolate gaps
        known = [i for i, t in enumerate(times) if t is not None]
        for i in range(len(times)):
            if times[i] is None:
                prev = max([k for k in known if k < i], default=None)
                nxt = min([k for k in known if k > i], default=None)
                if prev is None:
                    times[i] = times[nxt] if nxt is not None else 0.0
                elif nxt is None:
                    times[i] = times[prev] + 0.3 * (i - prev)
                else:
                    times[i] = times[prev] + (times[nxt] - times[prev]) * (i - prev) / (nxt - prev)
        self.times = times
        self.coverage = len(known) / max(1, len(a))

    def __call__(self, phrase, occ=0):
        i = -1
        for _ in range(occ + 1):
            i = self.text.find(phrase, i + 1)
            if i < 0:
                raise KeyError(phrase)
        for k, (_, ch) in enumerate(self.st):
            if ch >= i:
                return self.times[k]
        return self.times[-1]
