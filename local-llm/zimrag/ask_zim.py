#!/usr/bin/env python3
"""
ask_zim.py - Ask the offline ZIM corpus a question and get a cited answer.

Runs on Windows against Ollama; nothing here needs WSL. Drop .zim files into
E:\\LocalLLM\\zims and they are searchable immediately - there is no index to
build, because Kiwix archives carry their own.

    python zimrag/ask_zim.py "what causes ocean acidification?"
    python zimrag/ask_zim.py --list
    python zimrag/ask_zim.py --sources-only "pH of the ocean surface"
    python zimrag/ask_zim.py --model srini-draft:4b --top-k 6 "how do carbon markets work?"
    python zimrag/ask_zim.py --json "..."            # for scripting

Defaults to `srini-tools:3b`, the fast factual/retrieval pick. Its baked-in
operator profile is only ~300 tokens, so it no longer competes meaningfully with
the retrieved sources for attention; `--model srini-vision:2b` trades some quality for
roughly 3x the speed.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import zimrag


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except OSError:
                pass

    p = argparse.ArgumentParser(description="Cited answers from offline ZIM archives.")
    p.add_argument("question", nargs="*")
    p.add_argument("--model", default=os.environ.get("LOCAL_LLM_MODEL", "srini-tools:3b"))
    p.add_argument("--top-k", type=int, default=zimrag.DEFAULT_TOP_K)
    p.add_argument("--chars", type=int, default=zimrag.DEFAULT_CHARS_PER_SOURCE,
                   help="Characters of article text per source.")
    p.add_argument("--max-tokens", type=int, default=800)
    p.add_argument("--think", action="store_true",
                   help="Expose the model's reasoning channel.")
    p.add_argument("--sources-only", action="store_true",
                   help="Retrieve and print sources without calling the model.")
    p.add_argument("--no-rerank", action="store_false", dest="rerank",
                   help="Skip the embedding rerank; keep lexical order.")
    p.add_argument("--list", action="store_true", dest="list_corpus",
                   help="Show the ZIM corpus and exit.")
    p.add_argument("--include-testdata", action="store_true",
                   help="Also search zimrag/testdata (sample archives).")
    p.add_argument("--json", action="store_true", dest="as_json")
    args = p.parse_args()

    if args.list_corpus:
        paths = zimrag.available_zims(args.include_testdata)
        if not paths:
            print(f"No .zim files in {zimrag.ZIM_DIR}")
            print("Get archives from https://download.kiwix.org/zim/")
            return 1
        total = 0.0
        articles = 0
        print(f"{'file':<52} {'size':>8} {'articles':>10}  fulltext")
        for path in paths:
            d = zimrag.describe(path)
            total += d["size_gb"]
            articles += d["articles"]
            print(f"{d['file'][:52]:<52} {d['size_gb']:>7.2f}G "
                  f"{d['articles']:>10,}  {'yes' if d['fulltext'] else 'NO'}")
        print(f"\n{len(paths)} archive(s), {total:.2f} GB, {articles:,} articles")
        return 0

    question = " ".join(args.question).strip()
    if not question:
        p.error("ask a question, or use --list")

    if args.sources_only:
        try:
            sources = zimrag.search(question, top_k=args.top_k,
                                    chars_per_source=args.chars,
                                    include_testdata=args.include_testdata,
                                    rerank=args.rerank)
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        if args.as_json:
            print(json.dumps([s.__dict__ for s in sources], indent=2,
                             ensure_ascii=False))
            return 0
        if not sources:
            print("No matches.")
            return 1
        for s in sources:
            print(f"\n=== {s.citation}")
            print(s.text[:600])
        return 0

    try:
        r = zimrag.answer(question, model=args.model, top_k=args.top_k,
                          chars_per_source=args.chars, think=args.think,
                          max_tokens=args.max_tokens,
                          include_testdata=args.include_testdata,
                          rerank=args.rerank)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.as_json:
        out = dict(r)
        out["sources"] = [s.__dict__ for s in r["sources"]]
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 1 if r.get("error") else 0

    if r.get("error"):
        print(f"ERROR: {r['error']}", file=sys.stderr)
        return 1

    if r.get("thinking"):
        print(f"--- thinking ---\n{r['thinking']}\n--- answer ---")
    print(r["content"] or "(empty - raise --max-tokens)")

    # No sources means the model was never called, so there are no timings to
    # report - printing them would show a row of Nones.
    if not r["sources"]:
        return 1

    print("\nSources:")
    for s in r["sources"]:
        print(f"  {s.citation}  ({s.path})")
    print(f"\n[{r.get('model')} | {r.get('tokens_per_sec')} tok/s | "
          f"{r.get('wall_seconds')}s | {len(r['sources'])} source(s)]",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
