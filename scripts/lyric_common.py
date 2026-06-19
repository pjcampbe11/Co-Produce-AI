"""lyric_common.py - shared text helpers for the lyric scripts (stdlib only)."""

# ---------------------------------------------------------------------------
# Operator notes (the non-obvious bits):
#   - Heuristic helpers: syllables = vowel groups; rime = last vowel+coda; mood = small lexicon.
#   - These are approximations (not phonetic-perfect) - good enough for style profiling, not scansion.
# ---------------------------------------------------------------------------
import re
from collections import Counter

SECTION_RE = re.compile(r"^\s*[\[\(]?\s*(intro|verse|hook|chorus|bridge|outro|pre[- ]?chorus|refrain)\b",
                        re.IGNORECASE)
WORD_RE = re.compile(r"[a-z']+")
VOWELS = "aeiouy"
STOPWORDS = set("the a an and or but if then to of in on at for with my your i you he she it we they "
                "me him her them is am are was were be been being do does did this that these those "
                "as so just got get like im ima gonna wanna cause cuz yeah uh na la oh ay aint dont "
                "aint not no yes up down out all on off". split())

MOOD_LEX = {
    "dark": "dark death cold grave blood shadow pain demon hell night cry alone empty numb haunt",
    "aggressive": "kill gun smoke war beef strap clip rage fight blast murder savage threat",
    "triumphant": "win king crown throne rise top boss champion shine grind victory made",
    "reflective": "time life mind soul memory remember dream think change god pray lesson growth",
    "party": "club bottle dance party drink turn vibe night lit ride flex bands",
    "romantic": "love heart girl baby kiss touch need miss feel together forever",
    "sad": "tears lonely lost broken cry hurt gone miss regret sorry sorrow",
}
MOOD_WORDS = {m: set(w.split()) for m, w in MOOD_LEX.items()}


def count_syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    g = re.findall(r"[aeiouy]+", w)
    n = len(g)
    if w.endswith("e") and n > 1:
        n -= 1
    return max(n, 1)


def rime(word):
    """Final rime (last vowel group + trailing consonants) - crude rhyme key."""
    w = re.sub(r"[^a-z]", "", word.lower())
    m = re.search(r"[aeiouy]+[^aeiouy]*$", w)
    return m.group(0) if m else w


def last_words(line):
    ws = WORD_RE.findall(line.lower())
    return ws[-1] if ws else ""


def split_sections(text):
    """Return list of (section_type, [lines]). Uses headers if present, else blank-line stanzas."""
    lines = text.splitlines()
    has_headers = any(SECTION_RE.match(l) for l in lines)
    sections, cur_type, cur = [], "verse", []
    if has_headers:
        for l in lines:
            m = SECTION_RE.match(l)
            if m:
                if cur:
                    sections.append((cur_type, cur)); cur = []
                cur_type = m.group(1).lower().replace("pre-chorus", "prechorus")
            elif l.strip():
                cur.append(l.rstrip())
        if cur:
            sections.append((cur_type, cur))
    else:
        stanza = []
        for l in lines:
            if l.strip():
                stanza.append(l.rstrip())
            elif stanza:
                sections.append(("verse", stanza)); stanza = []
        if stanza:
            sections.append(("verse", stanza))
    return [(t, ls) for t, ls in sections if ls]


def analyze_lines(lines):
    """Per-section metrics."""
    syl = [sum(count_syllables(w) for w in WORD_RE.findall(l)) for l in lines]
    ends = [rime(last_words(l)) for l in lines if last_words(l)]
    # adjacent end-rhyme rate
    pairs = sum(1 for a, b in zip(ends, ends[1:]) if a and a == b)
    rhyme_rate = pairs / max(len(ends) - 1, 1)
    words = [w for l in lines for w in WORD_RE.findall(l.lower())]
    ttr = len(set(words)) / max(len(words), 1)
    return {
        "lines": len(lines),
        "avg_syllables_per_line": round(sum(syl) / max(len(syl), 1), 1),
        "end_rhyme_rate": round(rhyme_rate, 2),
        "type_token_ratio": round(ttr, 3),
        "words": len(words),
    }


def mood_of(words):
    c = Counter()
    wl = [w for w in words]
    wset = wl
    for m, lex in MOOD_WORDS.items():
        c[m] = sum(1 for w in wset if w in lex)
    top = [m for m, n in c.most_common(3) if n > 0]
    return top, dict(c)


def top_themes(words, k=15):
    c = Counter(w for w in words if w not in STOPWORDS and len(w) > 2)
    return [w for w, _ in c.most_common(k)]
