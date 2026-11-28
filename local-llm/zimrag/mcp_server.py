#!/usr/bin/env python3
"""MCP stdio server exposing zimrag.search() as a tool for a local LLM.

Read-only wrapper: does not touch zimrag.py/ask_zim.py. Retrieval is slow
(BM25 across 40 ZIMs can take minutes), so there is nothing to optimize here
except not re-opening archives - zimrag.corpus() is already lru_cached, and
importing zimrag once at module load (not per-call) keeps that cache warm
for the life of this process.
"""

from __future__ import annotations

import datetime
import inspect
import os
import sys
import threading
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from mcp.server.mcpserver import MCPServer

import zimrag

CHAR_BUDGET = 8000  # ~2000 tokens, bounding a local model's context window
MAX_TOP_K = 10

# Overridable so two test runs can measure in parallel without clobbering each
# other's ground truth - this log is the ONLY reliable proof a retrieval happened.
LOG_FILE = Path(os.environ.get("ZIM_MCP_LOG") or (HERE / "mcp_calls.log"))


def _log(msg: str) -> None:
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
    except OSError:
        pass  # stdout/stderr belong to the MCP transport; never fail a call to log


server = MCPServer("zimrag")

# zimrag.search() is gaining a keyword-only `rerank` param concurrently;
# tolerate its absence instead of hardcoding the new signature.
_SEARCH_PARAMS = set(inspect.signature(zimrag.search).parameters)


_CACHE_LOCK = threading.Lock()


@lru_cache(maxsize=64)
def _cached_search(query: str, top_k: int, zim_count: int) -> list:
    kwargs: dict = {"top_k": top_k}
    if "rerank" in _SEARCH_PARAMS:
        kwargs["rerank"] = True
    return list(zimrag.search(query, **kwargs))


@server.tool(
    description=(
        "Search a 441 GB offline corpus of 41 Kiwix ZIM archives (Wikipedia, "
        "Stack Overflow, devdocs, Arch wiki, libretexts textbooks, Project "
        "Gutenberg) for factual, reference, or documentation knowledge, when "
        "offline or when the answer needs a citation. Also covers command-line "
        "tools: what a command, flag, or option does, and its exact semantics. "
        "Returns up to ~8000 characters of cited passages, each tagged with "
        "archive and path."
    )
)
def zim_search(query: str, top_k: int = 5) -> str:
    """Search the offline ZIM corpus and return cited, budgeted passages."""
    # Log every call. Without this there is no way to tell a real retrieval from
    # a model answering out of its weights and inventing a "[1]" - which is
    # exactly what srini-draft:4b did before the directive was added.
    _log(f"zim_search query={query!r} top_k={top_k}")
    top_k = max(1, min(top_k, MAX_TOP_K))
    try:
        with _CACHE_LOCK:
            sources = [replace(s) for s in _cached_search(query.strip(), top_k, len(zimrag.available_zims()))]
    except Exception as e:  # noqa: BLE001 - never crash the MCP server on a bad/slow query
        return f"zim_search error: {e}"

    if not sources:
        return "No matches found in the ZIM corpus for that query."

    budget_each = max(200, CHAR_BUDGET // len(sources))
    blocks = []
    used = 0
    for s in sources:
        remaining = CHAR_BUDGET - used
        if remaining <= 0:
            break
        take = min(budget_each, remaining)
        text = s.text[:take]
        block = f"[{s.n}] {s.title} ({s.zim}:{s.path})\n{text}"
        blocks.append(block)
        used += len(block)

    # Format rules ride WITH the passages, not in the system prompt. Putting them
    # in the proxy's directive took srini-vision:2b from 6/6 tool calls to 2/4, while
    # here they cost nothing until a retrieval actually happens and they are the
    # last thing read before the answer. Both failures below are measured
    # 2026-11-25 on srini-vision:2b: it cited "[12] [13] [14]" against a 5-passage
    # result, and invented the link https://zimrag.example.com/Mercury_(Element)
    # for a local archive that has no web address at all.
    footer = (f"\n\n---\n[how to cite] Use only these numbers, 1 to {len(blocks)}, "
              f"one per bracket: [1], or [1][2] for two. Never join them as [12] "
              f"and never invent a number. These are local files with no URL - "
              f"name the archive and path, never a link.")
    out = "\n\n---\n\n".join(blocks)
    return out[:CHAR_BUDGET - len(footer)] + footer


if __name__ == "__main__":
    server.run("stdio")
