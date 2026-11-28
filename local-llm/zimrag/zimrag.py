#!/usr/bin/env python3
"""
zimrag.py - Cited, grounded answers from offline ZIM archives.

Why this exists: a 4B/9B local model cannot hold encyclopedia facts in its
weights. Measured on this machine, training 745 code facts into a LoRA produced
19% exact recall - four in five specifics confidently wrong. Retrieval fixes the
category error: the facts arrive in the prompt, with a citation, and the model's
job is reading rather than remembering.

No index is built. Kiwix ZIMs ship their own Xapian full-text index
(`Archive.has_fulltext_index`), so a query spans the whole corpus immediately -
nothing to rebuild when a file is added, no second copy of a 100 GB archive on
disk. One `Searcher` PER ARCHIVE, never one over several: a multi-archive
Searcher mismaps the `archive` attribute on its results, which silently dropped
every hit. See search().

Semantic rerank is query-time only. Embedding the corpus would be ~250M chunks,
about 375 GB of vectors and a week of GPU; embedding the ~30 candidates BM25
already found costs 0.5s and covers all 441 GB.

Pipeline per question:

    search all ZIMs      -> ranked articles (libzim's own BM25-ish ranking)
    fetch + strip HTML   -> plain text
    passage rerank       -> the paragraphs that actually contain the query terms
    grounded prompt      -> numbered sources, cite-or-say-you-cannot
    local model          -> answer with [n] citations

Used by ask_zim.py; importable for an MCP server or anything else.
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from itertools import zip_longest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ZIM_DIR = HERE.parent / "zims"
TESTDATA = HERE / "testdata"

# Default budget. 9B at 32k context could take far more, but retrieved text is
# the slowest part of generation and relevance drops fast after a few articles -
# more context mostly buys latency.
DEFAULT_TOP_K = 4
DEFAULT_CHARS_PER_SOURCE = 1600

# BM25/term-overlap ranking fails on paraphrase: "how do I undo my last commit"
# shares no words with "git reset". An embedding rerank over a wider candidate
# pool fixes that, but only if the embedder is reachable - see search()'s
# fallback to lexical order.
_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
if not _OLLAMA_HOST.startswith("http"):
    _OLLAMA_HOST = f"http://{_OLLAMA_HOST}"
EMBED_URL = f"{_OLLAMA_HOST.rstrip('/')}/api/embed"
EMBED_MODEL = "srini-embed"
EMBED_CHARS = 2000  # truncate so one huge article doesn't dominate the request
RERANK_OVERFETCH = 6  # candidates fetched per top_k slot before reranking

_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"(?is)<(script|style|noscript)\b.*?</\1>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_BLANK_RE = re.compile(r"\n{3,}")
_WORD_RE = re.compile(r"[a-z0-9]{3,}")

# Wikipedia boilerplate that survives tag stripping and wastes context.
_NOISE = re.compile(
    r"(?i)^(references|external links|see also|further reading|notes|"
    r"bibliography|citations|sources)$"
)

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "it", "this", "that", "these",
    "those", "as", "at", "by", "from", "what", "which", "who", "how", "why",
    "when", "does", "do", "did", "can", "could", "would", "should", "about",
    "there", "their", "them", "its", "into", "than", "then", "also", "more",
}


@dataclass
class Source:
    """One retrieved article, trimmed to the passages that answer the query."""

    n: int
    zim: str
    title: str
    path: str
    text: str
    snippet: str = ""

    @property
    def citation(self) -> str:
        return f"[{self.n}] {self.title} - {self.zim}"


def available_zims(include_testdata: bool = False) -> list[Path]:
    """Every .zim in zims/, newest last so a refreshed dump sorts after an old one."""
    paths = sorted(ZIM_DIR.glob("*.zim")) if ZIM_DIR.is_dir() else []
    if include_testdata and TESTDATA.is_dir():
        paths += sorted(TESTDATA.glob("*.zim"))
    return paths


@lru_cache(maxsize=32)
def _open(path_str: str):
    """Archives are cached: opening a multi-GB ZIM per query is wasteful."""
    from libzim.reader import Archive

    return Archive(path_str)


def corpus(include_testdata: bool = False) -> list:
    return [_open(str(p)) for p in available_zims(include_testdata)]


def describe(path: Path) -> dict:
    """Metadata for `--list`, without reading the whole archive."""
    a = _open(str(path))
    out = {
        "file": path.name,
        "size_gb": round(path.stat().st_size / 1e9, 2),
        "articles": a.article_count,
        "fulltext": a.has_fulltext_index,
    }
    for key in ("Title", "Date", "Language", "Flavour"):
        try:
            out[key.lower()] = a.get_metadata(key).decode("utf-8", "replace")
        except (RuntimeError, KeyError):
            pass
    return out


def strip_html(raw: str) -> str:
    """HTML to readable text, dropping the parts that only cost context."""
    text = _SCRIPT_RE.sub(" ", raw)
    text = re.sub(r"(?i)</(p|div|h[1-6]|li|tr|section)>", "\n", text)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = unicodedata.normalize("NFKC", text)
    text = _WS_RE.sub(" ", text)

    kept: list[str] = []
    for line in (ln.strip() for ln in text.split("\n")):
        if not line or _NOISE.match(line):
            continue
        kept.append(line)
    return _BLANK_RE.sub("\n\n", "\n".join(kept)).strip()


_STUB_RE = re.compile(r'(?i)<meta\s+http-equiv="refresh"')
_PAGE_ID_RE = re.compile(r"page_(\d+)\b")


def spa_text(archive, path: str) -> str:
    """Article text for single-page-app archives, which hide it from the entry.

    Not every ZIM stores one HTML document per article. LibreTexts (and other
    scrapers of JavaScript sites) index a stub - 280 bytes of
    `<meta http-equiv="refresh">` pointing at `index.html#/...` - while the real
    document sits in a sibling JSON blob, `content/page_content_<id>.json`
    against a stub at `index/page_<id>`. The Xapian index covers the real text,
    so these articles rank correctly and then extract to nothing, which is the
    worst combination: confident retrieval of empty sources.
    """
    m = _PAGE_ID_RE.search(path)
    if not m:
        return ""
    try:
        item = archive.get_entry_by_path(
            f"content/page_content_{m.group(1)}.json").get_item()
        data = json.loads(bytes(item.content).decode("utf-8", "replace"))
    except (RuntimeError, KeyError, ValueError, UnicodeDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    # The payload key is `htmlBody` today; take every string value so a
    # renamed or split field does not silently yield nothing.
    return strip_html("\n".join(v for v in data.values() if isinstance(v, str)))


def query_terms(question: str) -> set[str]:
    return {w for w in _WORD_RE.findall(question.lower()) if w not in STOPWORDS}


def ranked_terms(question: str) -> list[str]:
    """Content terms, most specific first.

    Specificity is approximated by length, with a boost for words capitalised in
    the original question - those are usually the proper nouns that carry the
    query. Without index statistics this is the cheapest usable proxy for IDF.
    """
    seen: set[str] = set()
    scored: list[tuple[float, str]] = []
    for raw in re.findall(r"[A-Za-z0-9]{3,}", question):
        low = raw.lower()
        if low in STOPWORDS or low in seen:
            continue
        seen.add(low)
        score = len(low) + (2.0 if raw[:1].isupper() else 0.0)
        scored.append((score, low))
    scored.sort(key=lambda t: -t[0])
    return [w for _, w in scored]


# Words that name a quantity rather than the thing being asked about. Title
# search on these alone just returns "Boiling point" (the general concept
# article); stripping them leaves the entity term ("mercury") that the title
# index can resolve directly.
GENERIC_QUANTITY_WORDS = {
    "boiling", "melting", "freezing", "point", "mass", "distance", "population",
    "speed", "velocity", "height", "weight", "length", "radius", "diameter",
    "temperature", "altitude", "area", "volume", "age", "density", "pressure",
    "celsius", "fahrenheit", "kelvin", "degrees", "degree",
}

_QUANTITY_Q_RE = re.compile(
    r"(?i)\b(boiling point|melting point|freezing point|mass|distance|"
    r"population|speed|velocity|height|weight|length|radius|diameter|"
    r"temperature|altitude|area|volume|density|pressure|"
    r"how (?:many|much|far|tall|heavy|hot|cold|fast|old))\b"
)


def wants_quantity(question: str) -> bool:
    """True for 'what is the X of Y' questions whose answer is a number with a
    unit, not prose - best_passages then favours a paragraph carrying one over
    one that merely shares more query words."""
    return bool(_QUANTITY_Q_RE.search(question))


# Loose on purpose: a trailing 1-3 letter unit token, a degree mark, or %.
# False positives (page numbers, years) just add a small bonus alongside term
# overlap, so they only win when nothing else in the article matches better.
_NUMBER_UNIT_RE = re.compile(
    r"(?i)[-+]?\d[\d,]*\.?\d*\s?(?:°\s?[cfk]\b|degrees?\b|%|km/h|mph|"
    r"kg|km|mi|mm|cm|ml|kcal|lbs?|tons?|million|billion|trillion|[a-z]{1,3}\b)"
)


def _entity_terms(question: str) -> list[str]:
    terms = [t for t in ranked_terms(question) if t not in GENERIC_QUANTITY_WORDS]
    return terms or ranked_terms(question)


class _TitleHit:
    """Stands in for a libzim search result so the main fetch loop in search()
    can treat title-index hits exactly like full-text ones."""
    __slots__ = ("archive", "path", "snippet", "title")

    def __init__(self, archive, path, title):
        self.archive = archive
        self.path = path
        self.title = title
        self.snippet = ""


def _title_candidates(question: str, archives: list, max_terms: int = 2,
                       max_suggestions: int = 500) -> list:
    """Title-index channel, separate from full-text BM25.

    Full-text search is AND-only and ranks by term overlap, so "boiling point
    of mercury" pulls in thermometer/instrument articles that mention all four
    words rather than the element's own page - measured, see the module
    docstring's failure case. The title index resolves the entity term
    directly; SuggestionSearcher.suggest("mercury") ranks "Mercury" (the
    disambiguation page) first and "Mercury_(Element)" 124th, so take the bare
    title and every parenthetical-qualified variant and let semantic rerank -
    not a guess here - pick the right sense.
    """
    from libzim.suggestion import SuggestionSearcher

    terms = _entity_terms(question)[:max_terms]
    hits = []
    for a in archives:
        if not getattr(a, "has_title_index", False):
            continue
        searcher = SuggestionSearcher(a)
        for term in terms:
            prefix = term.lower()
            try:
                paths = list(searcher.suggest(term)
                             .get_results(0, max_suggestions))
            except RuntimeError:
                continue
            for p in paths:
                low = p.lower().replace("_", " ")
                if low != prefix and not low.startswith(prefix + " ("):
                    continue
                try:
                    entry = a.get_entry_by_path(p)
                    if entry.is_redirect:
                        entry = entry.get_redirect_entry()
                except (RuntimeError, KeyError):
                    continue
                hits.append(_TitleHit(a, p, entry.title))
    return hits


def _search_backoff(searcher, question: str, max_terms: int = 5):
    """Search with progressive relaxation, returning (results, query_used).

    ZIM full-text indexes are built with AND semantics: every term must appear,
    so a natural-language question matches nothing at all. Measured on a climate
    ZIM, "ocean acidification" finds 53 articles, adding "pH" leaves 6, and the
    whole question "what causes ocean acidification and how much has pH fallen?"
    finds 0.

    Xapian's own operators are not reliably honoured through this wrapper
    ("a OR b OR c" returned 0 matches), so relaxation is done here instead:
    start with the most specific terms and drop one at a time until the index
    returns something. The first non-empty result set is also the most
    constrained one, which is what ranks best.
    """
    from libzim.search import Query

    terms = ranked_terms(question)
    if not terms:
        terms = [question.strip()]

    for k in range(min(max_terms, len(terms)), 0, -1):
        q = " ".join(terms[:k])
        results = searcher.search(Query().set_query(q))
        if results.get_estimated_matches():
            return results, q
    return None, " ".join(terms[:1])


def best_passages(text: str, terms: set[str], budget: int,
                   want_quantity: bool = False) -> str:
    """The paragraphs that actually mention the query, up to `budget` chars.

    The ZIM index ranks *articles*; within a long article the answer may be in
    one paragraph near the bottom. Sending the first N characters instead would
    often send the lead section and miss it entirely.

    `want_quantity` biases toward a paragraph carrying a number-with-unit: in
    a 100k-char article, the paragraph with "356.73 °C" may share almost no
    words with "boiling point of mercury celsius" (it reads "...vaporises at
    356.73 degrees..."), so pure term overlap ranks it below paragraphs that
    merely talk about thermometers using all four query words.
    """
    paras = [p for p in text.split("\n") if len(p) > 40]
    if not paras:
        paras = [p for p in text.split("\n") if len(p) > 15]
    if not paras:
        return text[:budget]

    scored: list[tuple[float, int, str]] = []
    for i, para in enumerate(paras):
        words = set(_WORD_RE.findall(para.lower()))
        hits = len(terms & words)
        # Keep the lead paragraph in contention: it defines the subject, which
        # is usually needed even when the specific detail lives further down.
        lead_bonus = 1.5 if i == 0 else 0.0
        quantity_bonus = 3.0 if (want_quantity and hits > 0 and _NUMBER_UNIT_RE.search(para)) else 0.0
        scored.append((hits + lead_bonus + quantity_bonus, i, para))

    scored.sort(key=lambda t: (-t[0], t[1]))
    chosen: list[tuple[int, str]] = []
    used = 0
    for score, i, para in scored:
        if score == 0 and chosen:
            break
        if used + len(para) > budget and chosen:
            continue
        chosen.append((i, para))
        used += len(para)
        if used >= budget:
            break

    chosen.sort(key=lambda t: t[0])  # restore document order for readability
    return "\n\n".join(p for _, p in chosen)[:budget]


def _embed_batch(texts: list[str]) -> list[list[float]]:
    """One batched call to Ollama's embedder. Raises on any failure - callers
    must catch and fall back, since this is an optional local service."""
    body = json.dumps({"model": EMBED_MODEL, "input": texts}).encode("utf-8")
    req = urllib.request.Request(
        EMBED_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    embeddings = data["embeddings"]
    if len(embeddings) != len(texts):
        raise ValueError(f"expected {len(texts)} embeddings, got {len(embeddings)}")
    return embeddings


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _rerank_semantic(question: str, sources: list[Source]) -> list[Source]:
    """Reorder candidates by cosine similarity to the question, not term
    overlap. Raises on any embedder problem; search() catches it and keeps
    the lexical order instead."""
    texts = [question] + [s.text[:EMBED_CHARS] for s in sources]
    vecs = _embed_batch(texts)
    q_vec, s_vecs = vecs[0], vecs[1:]
    scored = sorted(zip(s_vecs, sources, strict=True), key=lambda t: -_cosine(q_vec, t[0]))
    return [s for _, s in scored]


def search(question: str, *, top_k: int = DEFAULT_TOP_K,
           chars_per_source: int = DEFAULT_CHARS_PER_SOURCE,
           include_testdata: bool = False, rerank: bool = True) -> list[Source]:
    """Rank articles across every ZIM, then trim each to its useful passages."""
    from libzim.search import Searcher

    archives = corpus(include_testdata)
    if not archives:
        raise FileNotFoundError(
            f"no .zim files found in {ZIM_DIR}\n"
            f"Put archives there (see https://download.kiwix.org/zim/) and retry."
        )

    # One Searcher per archive, never one Searcher over many. A multi-archive
    # Searcher mismaps the `archive` attribute on its results: it returned the
    # stackoverflow path "questions/33849704/git-reset-vs-git-reset-head" paired
    # with the *serverfault* archive, so get_entry_by_path below raised KeyError
    # for every hit and the loop silently dropped them all. Measured 2026-11-25:
    # 40,000 index matches for "git reset" produced 0 sources.
    matched: list = []
    for a in archives:
        # A single-archive Searcher raises "Cannot create Search without FT
        # Xapian index" on an unindexed archive (phet), where the multi-archive
        # one silently tolerated it. --list shows which lack an index.
        if not a.has_fulltext_index:
            continue
        res, q = _search_backoff(Searcher(a), question)
        if res is not None:
            matched.append((res, q))

    title_hits = _title_candidates(question, archives)

    if not matched and not title_hits:
        return []

    if matched:
        # Prefer the most specific query any archive could satisfy, while keeping
        # (best - 1)-term hits so a 107 GB archive matching 2 terms doesn't drop
        # an exact 1-term match from a smaller specialized ZIM (devdocs/archwiki).
        best = max(len(q.split()) for _, q in matched)
        min_terms = max(1, best - 1)
        matched = [(r, q) for r, q in matched if len(q.split()) >= min_terms]

        # Over-fetch: redirects and stubs get dropped, and a short article may
        # contribute nothing after passage selection. Rerank needs a wider pool
        # too, since the lexical pre-filter is exactly what a paraphrase evades.
        fetch_n = max(top_k * RERANK_OVERFETCH, 30) if rerank else top_k
        want = max(fetch_n * 3, fetch_n + 4)
        batches = [list(r.get_results(0, want)) for r, _ in matched]
        # Round-robin, so a 107 GB archive cannot crowd out a 2 MB devdocs one.
        ranked = [x for row in zip_longest(*batches) for x in row if x is not None]
    else:
        fetch_n = max(top_k * RERANK_OVERFETCH, 30) if rerank else top_k
        ranked = []

    terms = query_terms(question)
    want_quantity = wants_quantity(question)
    # Round-robin alone orders by archive name, which put an Arch Linux modem
    # page first for "git reset". Each archive ranks its own hits but the index
    # exposes no cross-archive score, so re-rank on how many query terms the
    # title and snippet actually contain. Stable, so ties keep archive diversity.
    def _relevance(x) -> int:
        blob = f"{x.title or ''} {strip_html(x.snippet or '')}".lower()
        return len(terms & set(_WORD_RE.findall(blob)))

    ranked.sort(key=_relevance, reverse=True)
    # Title-index hits go first, ahead of BM25: they are the entity's own
    # article, picked by title rather than by how many query words it shares,
    # so BM25's term-overlap sort must not be allowed to bury or drop them.
    #
    # But only let them LEAD an entity question. Promoted unconditionally they
    # wrecked "git reset": title matching returned the generic "Git" wiki page
    # and "Reset (military)" ahead of devdocs' own git-reset article, which BM25
    # had ranked first. For a term or command lookup, full text is the better
    # signal; title hits still ride along at the back so the semantic rerank can
    # pull one up if it really is the answer.
    seen = {(Path(x.archive.filename).name, x.path) for x in ranked}
    fresh = [h for h in title_hits
             if (Path(h.archive.filename).name, h.path) not in seen]
    ranked = fresh + ranked if want_quantity else ranked + fresh
    sources: list[Source] = []
    seen_targets: set[tuple[str, str]] = set()
    for r in ranked:
        if len(sources) >= fetch_n:
            break
        zim_name = Path(r.archive.filename).name
        try:
            entry = r.archive.get_entry_by_path(r.path)
            if entry.is_redirect:
                entry = entry.get_redirect_entry()
            if (zim_name, entry.path) in seen_targets:
                continue
            seen_targets.add((zim_name, entry.path))
            item = entry.get_item()
            if "html" not in (item.mimetype or ""):
                continue
            raw = bytes(item.content).decode("utf-8", "replace")
        except (RuntimeError, KeyError, UnicodeDecodeError):
            continue

        body = strip_html(raw)
        if len(body) < 200 or _STUB_RE.search(raw):
            body = spa_text(r.archive, r.path) or body
        # Last resort: the index's own highlighted excerpt. Short, but real text
        # from a real match beats dropping a correctly-ranked article.
        if len(body) < 80:
            body = strip_html(r.snippet or "")

        text = best_passages(body, terms, chars_per_source, want_quantity)
        if len(text) < 80:
            continue
        sources.append(Source(
            n=len(sources) + 1,
            zim=Path(r.archive.filename).name,
            title=r.title or entry.title or r.path,
            path=r.path,
            text=text,
            snippet=strip_html(r.snippet or "")[:300],
        ))

    if rerank and len(sources) > 1:
        try:
            sources = _rerank_semantic(question, sources)
        except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError, KeyError):
            pass  # embedder down/missing/wrong shape - keep lexical order

    sources = sources[:top_k]
    for i, s in enumerate(sources, start=1):
        s.n = i
    return sources


SYSTEM = (
    "You answer strictly from the numbered sources provided. Cite the source "
    "number in square brackets after each claim, like [1]. If the sources do "
    "not contain the answer, say exactly what is missing instead of guessing - "
    "an unsupported answer is worse than admitting the gap. Do not add facts "
    "from memory, and do not cite a source number that was not given to you."
)


def build_prompt(question: str, sources: list[Source]) -> str:
    blocks = [f"[{s.n}] {s.title} (from {s.zim})\n{s.text}" for s in sources]
    return (
        "Sources:\n\n" + "\n\n---\n\n".join(blocks)
        + f"\n\n---\n\nQuestion: {question}\n\n"
        "Answer using only the sources above, citing [n] for each claim."
    )


def answer(question: str, *, model: str = "srini-coder:9b", top_k: int = DEFAULT_TOP_K,
           chars_per_source: int = DEFAULT_CHARS_PER_SOURCE,
           think: bool = False, max_tokens: int = 800,
           include_testdata: bool = False, rerank: bool = True) -> dict:
    """Retrieve, then answer with citations. Returns the reply plus its sources."""
    parent_dir = str(HERE.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from ask_local_llm import ask

    sources = search(question, top_k=top_k, chars_per_source=chars_per_source,
                     include_testdata=include_testdata, rerank=rerank)
    if not sources:
        return {"question": question, "sources": [], "content":
                "Nothing in the ZIM corpus matched that question.", "error": None}

    reply = ask(
        build_prompt(question, sources),
        model=model,
        system=SYSTEM,
        think=think,
        max_tokens=max_tokens,
        temperature=0.2,          # grounded extraction, not invention
        num_ctx=16384,            # the prompt carries several articles
    )
    return {
        "question": question,
        "sources": sources,
        "content": reply.content,
        "thinking": reply.thinking,
        "model": reply.model,
        "tokens_per_sec": reply.tokens_per_sec,
        "wall_seconds": reply.wall_seconds,
        "error": reply.error,
    }
