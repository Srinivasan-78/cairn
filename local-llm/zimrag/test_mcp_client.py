#!/usr/bin/env python3
"""Standalone client: launches mcp_server.py over stdio and drives it.

Verifies the handshake, tools/list, a real query, and the no-results path.
Run with: python E:\\LocalLLM\\zimrag\\test_mcp_client.py
"""

import io
import sys

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

# Windows consoles default to cp1252, so printing a retrieved passage crashed on
# the first non-Latin-1 character (a macron in a Maori place name). The corpus is
# 70M articles of UTF-8; any test that prints passages must say so.
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SERVER = StdioServerParameters(command="python", args=["E:\\LocalLLM\\zimrag\\mcp_server.py"])


async def main() -> None:
    async with stdio_client(SERVER) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        print("=== handshake OK ===")

        tools = await session.list_tools()
        print("=== tools/list ===")
        for t in tools.tools:
            print(f"  {t.name}: {t.description}")

        print("\n=== zim_search('git reset --hard', top_k=2) ===")
        result = await session.call_tool(
            "zim_search",
            {"query": "git reset --hard", "top_k": 2},
            read_timeout_seconds=120,
        )
        text = "".join(
            c.text for c in result.content if isinstance(c, TextContent)
        )
        print(f"length: {len(text)} chars")
        print(text[:600])

        # Every term must be gibberish. The old query was "qzxjklvwplonk
        # nonsense query zzyx", and _search_backoff dropped the gibberish and
        # matched real articles on "nonsense"/"query" - so this stopped
        # testing the no-results path and started testing backoff instead.
        print("\n=== zim_search(all-gibberish) ===")
        result2 = await session.call_tool(
            "zim_search",
            {"query": "qzxjklvwplonk zzyxwq vmbplkj"},
            read_timeout_seconds=120,
        )
        text2 = "".join(
            c.text for c in result2.content if isinstance(c, TextContent)
        )
        print(f"isError: {result2.is_error}")
        print(text2)
        assert not result2.is_error, "no-match path must not raise"
        assert "No matches" in text2, f"expected a no-match message, got {text2[:200]!r}"


if __name__ == "__main__":
    anyio.run(main)
