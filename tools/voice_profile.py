#!/usr/bin/env python3
"""
DS Voice Profiler — measures a writer's style so edits can stay in their voice.

Usage:
  python3 voice_profile.py profile  SAMPLE.txt [SAMPLE2.txt ...]   > profile.json
  python3 voice_profile.py report   SAMPLE.txt [...]                 (human-readable profile)
  python3 voice_profile.py drift    profile.json  ORIGINAL.txt  EDITED.txt
      -> shows where an edited version moves away from the writer's measured style
         (new vocabulary, new connectives, sentence-length shift, generic stock phrases introduced)

Pure standard library. Text in, numbers out. It never rewrites anything itself.
"""
import json, re, statistics, sys
from collections import Counter

# ---------------------------------------------------------------- word lists
CONNECTIVES = [
    "however", "moreover", "furthermore", "additionally", "in addition", "therefore", "thus", "hence",
    "consequently", "as a result", "nevertheless", "nonetheless", "although", "even though", "whereas",
    "while", "because", "since", "so", "but", "and also", "also", "for example", "for instance",
    "in conclusion", "overall", "in summary", "to sum up", "firstly", "secondly", "finally", "lastly",
    "on the other hand", "in contrast", "similarly", "likewise", "meanwhile", "instead", "in fact",
    "indeed", "notably", "importantly", "in this regard", "in other words", "that is",
]
HEDGES = ["may", "might", "could", "perhaps", "possibly", "likely", "unlikely", "appears", "appear",
          "seems", "seem", "suggests", "suggest", "indicates", "indicate", "tends", "tend", "probably",
          "somewhat", "partly", "to some extent", "arguably"]
BOOSTERS = ["clearly", "obviously", "definitely", "certainly", "undoubtedly", "always", "never",
            "very", "really", "extremely", "highly", "strongly", "crucial", "significantly", "huge",
            "greatly", "completely", "entirely", "must"]
# Generic stock phrasing that commonly enters text through automated rewriting. Used ONLY to stop
# edits from importing phrasing the writer does not use; it is not an authorship test.
STOCK_PHRASES = [
    "it is worth noting", "it is important to note", "plays a crucial role", "plays a pivotal role",
    "in today's", "in the modern world", "delve", "delves", "tapestry", "landscape of", "realm of",
    "underscores", "highlights the importance", "a testament to", "navigate the complexities",
    "multifaceted", "nuanced understanding", "foster", "fosters", "leverage", "leverages",
    "pivotal", "paramount", "seamless", "seamlessly", "robust", "holistic", "in this regard",
    "shed light on", "sheds light on", "ever-evolving", "game-changer", "at the end of the day",
    "serves as a", "not only", "it can be argued that", "this essay will", "in conclusion,",
]
PRONOUNS = {"first_singular": ["i", "me", "my", "mine", "myself"],
            "first_plural": ["we", "us", "our", "ours", "ourselves"],
            "second": ["you", "your", "yours"],
            "impersonal_one": ["one"]}
STOP = set("""a an the and or but if of to in on at by for with from as is are was were be been being
this that these those it its they them their he she his her we our you your i me my not no so than then
there here which who whom whose what when where why how all any some can could may might will would should
do does did done has have had also into about over under more most such only very just""".split())


# ---------------------------------------------------------------- text helpers
def clean(text):
    text = re.sub(r"https?://\S+", " ", text)            # drop URLs
    text = re.sub(r"\([^()]*\d{4}[^()]*\)", " ", text)     # drop (Author, 2024) citations
    text = re.sub(r"\[[^\]]*\]", " ", text)                 # drop [1] style citations
    return text.replace("​", " ").replace("’", "'").replace("“", '"').replace("”", '"')

def paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.split()) >= 12]

def sentences(text):
    flat = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'(])", flat)
    return [s.strip() for s in parts if len(s.split()) >= 3]

def words(text):
    return re.findall(r"[A-Za-z][A-Za-z'\-]*", text)

def syllables(w):
    w = w.lower().strip("'")
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups) - (1 if w.endswith("e") and len(groups) > 1 else 0)
    return max(1, n)

def count_phrase(lower, phrase):
    return len(re.findall(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", lower))

def mattr(tokens, window=100):
    if len(tokens) < window:
        return round(len(set(tokens)) / max(1, len(tokens)), 3)
    vals = [len(set(tokens[i:i + window])) / window for i in range(0, len(tokens) - window + 1, 10)]
    return round(statistics.mean(vals), 3)


# ---------------------------------------------------------------- profile
def build_profile(raw):
    text = clean(raw)
    sents, paras = sentences(text), paragraphs(text)
    toks = [w.lower() for w in words(text)]
    n = max(1, len(toks))
    per1k = lambda c: round(1000 * c / n, 2)
    lower = " " + re.sub(r"\s+", " ", text.lower()) + " "
    slens = [len(words(s)) for s in sents] or [0]

    passive = len(re.findall(r"\b(is|are|was|were|be|been|being)\s+(\w+ly\s+)?\w+(ed|en)\b", lower))
    openers = Counter(words(s)[0].lower() for s in sents if words(s))
    content = [t for t in toks if t not in STOP and len(t) > 2]
    bigrams = Counter(zip(content, content[1:]))
    trigrams = Counter(zip(toks, toks[1:], toks[2:]))

    prof = {
        "size": {"words": len(toks), "sentences": len(sents), "paragraphs": len(paras)},
        "sentence_length": {
            "mean": round(statistics.mean(slens), 1),
            "median": statistics.median(slens),
            "stdev": round(statistics.pstdev(slens), 1),
            "pct_short_<12": round(100 * sum(l < 12 for l in slens) / len(slens), 1),
            "pct_long_>30": round(100 * sum(l > 30 for l in slens) / len(slens), 1),
        },
        "paragraph_length_mean_words": round(statistics.mean([len(words(p)) for p in paras]), 1) if paras else 0,
        "vocabulary": {
            "mattr_lexical_diversity": mattr(toks),
            "mean_word_length": round(statistics.mean(len(t) for t in toks), 2) if toks else 0,
            "pct_words_3plus_syllables": round(100 * sum(syllables(t) >= 3 for t in toks) / n, 1),
        },
        "voice": {
            **{k: per1k(sum(toks.count(p) for p in v)) for k, v in PRONOUNS.items()},
            "passive_per_1k": per1k(passive),
            "contractions_per_1k": per1k(len(re.findall(r"\b\w+'(t|s|re|ve|ll|d|m)\b", text.lower()))),
            "questions_per_1k": per1k(text.count("?")),
        },
        "punctuation_per_sentence": {
            "commas": round(text.count(",") / max(1, len(sents)), 2),
            "semicolons": round(text.count(";") / max(1, len(sents)), 3),
            "colons": round(text.count(":") / max(1, len(sents)), 3),
            "dashes": round((text.count(" - ") + text.count("—") + text.count("–")) / max(1, len(sents)), 3),
            "parentheses": round(text.count("(") / max(1, len(sents)), 3),
        },
        "connectives_per_1k": {c: per1k(count_phrase(lower, c)) for c in CONNECTIVES if count_phrase(lower, c)},
        "hedges_per_1k": per1k(sum(count_phrase(lower, h) for h in HEDGES)),
        "boosters_per_1k": per1k(sum(count_phrase(lower, b) for b in BOOSTERS)),
        "stock_phrases_found": {p: count_phrase(lower, p) for p in STOCK_PHRASES if count_phrase(lower, p)},
        "top_sentence_openers": openers.most_common(12),
        "signature_bigrams": [(" ".join(k), v) for k, v in bigrams.most_common(15) if v > 1],
        "signature_trigrams": [(" ".join(k), v) for k, v in trigrams.most_common(25)
                               if v > 1 and not set(k) <= STOP][:12],
        "vocabulary_set": sorted(set(toks)),
    }
    return prof


def report(prof):
    p = dict(prof); p.pop("vocabulary_set", None)
    s, v, vo = p["sentence_length"], p["vocabulary"], p["voice"]
    out = [
        f"WORDS {p['size']['words']} · SENTENCES {p['size']['sentences']} · PARAGRAPHS {p['size']['paragraphs']}",
        f"Sentence length: mean {s['mean']} (median {s['median']}, sd {s['stdev']}); short<12: {s['pct_short_<12']}%; long>30: {s['pct_long_>30']}%",
        f"Paragraph length: ~{p['paragraph_length_mean_words']} words",
        f"Vocabulary: diversity {v['mattr_lexical_diversity']}, mean word length {v['mean_word_length']}, 3+ syllable words {v['pct_words_3plus_syllables']}%",
        f"Voice per 1k words: I/my {vo['first_singular']} · we/our {vo['first_plural']} · you {vo['second']} · passive {vo['passive_per_1k']} · contractions {vo['contractions_per_1k']}",
        f"Hedges/1k {p['hedges_per_1k']} · Boosters/1k {p['boosters_per_1k']}",
        f"Punctuation per sentence: {p['punctuation_per_sentence']}",
        "Connectives used (per 1k): " + ", ".join(f"{k} {v}" for k, v in sorted(p['connectives_per_1k'].items(), key=lambda x: -x[1])),
        "Sentence openers: " + ", ".join(f"{w}({c})" for w, c in p["top_sentence_openers"]),
        "Signature phrases: " + ", ".join(f"'{w}'({c})" for w, c in p["signature_trigrams"] + p["signature_bigrams"][:6]),
        "Stock phrases already in the writer's own text: " + (", ".join(f"'{k}'({c})" for k, c in p["stock_phrases_found"].items()) or "none"),
    ]
    return "\n".join(out)


# ---------------------------------------------------------------- drift check
def drift(profile, original, edited):
    o, e = build_profile(original), build_profile(edited)
    known = set(profile["vocabulary_set"]) | set(o["vocabulary_set"])
    new_words = sorted(w for w in set(e["vocabulary_set"]) - known if len(w) > 3 and w not in STOP)
    flags = []
    def cmp(label, a, b, tol):
        if a and abs(b - a) / max(abs(a), 1e-9) > tol:
            flags.append(f"{label}: writer {a} → edit {b}")
    cmp("Mean sentence length", profile["sentence_length"]["mean"], e["sentence_length"]["mean"], 0.20)
    cmp("3+ syllable words %", profile["vocabulary"]["pct_words_3plus_syllables"], e["vocabulary"]["pct_words_3plus_syllables"], 0.25)
    cmp("Passive per 1k", profile["voice"]["passive_per_1k"], e["voice"]["passive_per_1k"], 0.50)
    cmp("Boosters per 1k", profile["boosters_per_1k"], e["boosters_per_1k"], 0.50)
    cmp("Commas per sentence", profile["punctuation_per_sentence"]["commas"], e["punctuation_per_sentence"]["commas"], 0.35)
    new_conn = sorted(set(e["connectives_per_1k"]) - set(profile["connectives_per_1k"]) - set(o["connectives_per_1k"]))
    new_stock = sorted(set(e["stock_phrases_found"]) - set(profile["stock_phrases_found"]) - set(o["stock_phrases_found"]))
    ow, ew = set(o["vocabulary_set"]), set(e["vocabulary_set"])
    retention = round(100 * len(ow & ew) / max(1, len(ow)), 1)
    return {
        "word_retention_%": retention,
        "style_shifts": flags or ["none beyond tolerance"],
        "connectives_not_in_writer_profile": new_conn,
        "stock_phrases_introduced": new_stock,
        "vocabulary_not_in_writer_profile": new_words[:60],
    }


# ---------------------------------------------------------------- cli
def read(paths):
    return "\n\n".join(open(p, encoding="utf-8", errors="ignore").read() for p in paths)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    mode = sys.argv[1]
    if mode == "profile":
        print(json.dumps(build_profile(read(sys.argv[2:])), ensure_ascii=False, indent=1))
    elif mode == "report":
        print(report(build_profile(read(sys.argv[2:]))))
    elif mode == "drift":
        prof = json.load(open(sys.argv[2]))
        print(json.dumps(drift(prof, read([sys.argv[3]]), read([sys.argv[4]])), ensure_ascii=False, indent=1))
    else:
        sys.exit(__doc__)
