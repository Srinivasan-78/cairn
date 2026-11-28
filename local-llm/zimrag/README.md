# zimrag — cited answers from offline ZIM archives

Drop `.zim` files into `E:\LocalLLM\zims` and ask questions. **There is no index
to build**: Kiwix archives ship their own Xapian full-text index, and one
`Searcher` spans every archive at once, so a new file is searchable the moment
it finishes downloading.

```powershell
python zimrag\ask_zim.py --list
python zimrag\ask_zim.py "what causes ocean acidification?"
python zimrag\ask_zim.py --sources-only "pH of the ocean surface"   # no model call
python zimrag\ask_zim.py --model srini-draft:4b --top-k 6 "how do carbon markets work?"
python zimrag\ask_zim.py --json "..."                                # for scripting
```

Runs entirely on Windows against Ollama — no WSL, no GPU training, no embedding
pass.

## Why retrieval instead of training

Measured on this machine: fine-tuning 745 facts about the operator's own code
into a LoRA produced **19% exact identifier recall** — four in five specifics
confidently wrong (`IntegrityError` for `IntegrityReport`, invented repo URLs).
The model learned the *shape* of an answer, not its content.

Retrieval moves the facts into the prompt, where they are exact and attributable:

```
Q: what causes ocean acidification and how much has the ocean surface pH fallen?
A: Carbon dioxide emissions from human activities are the primary cause of ocean
   acidification [1]. The average pH of the ocean surface fell from approximately
   8.15 to 8.05 between 1950 and 2020 [1].
   [1] Ocean acidification — wikipedia_en_climate-change_mini
```

Those numbers are checkable against the cited article. And when the corpus does
not hold the answer it says so, rather than guessing:

```
Q: What is the population of Tokyo and its average commute time?
A: The provided sources do not contain information about the population of Tokyo
   or its average commute time. The text mentions Tokyo as a member of the C40
   steering committee but does not include demographic data [1].
```

## How it works

```
search all ZIMs      libzim Searcher over every archive, with query backoff
fetch + strip HTML   scripts/styles/nav removed, entities unescaped
passage rerank       the paragraphs that contain the query terms, in order
grounded prompt      numbered sources + cite-or-admit-the-gap instruction
local model          srini-coder:9b at temperature 0.2
```

Two non-obvious details carry most of the quality:

**Query backoff.** ZIM indexes use **AND** semantics, so a natural question
matches nothing. On the climate archive, `ocean acidification` finds 53
articles, `ocean acidification pH` leaves 6, and the full sentence *"what causes
ocean acidification and how much has pH fallen?"* finds **0**. Xapian's own
operators are not honoured reliably through the Python wrapper (`a OR b OR c`
returned 0), so `_search_backoff` ranks terms by specificity — length, plus a
boost for words capitalised in the question — and drops the least specific one
at a time until the index answers. The first non-empty result set is also the
most constrained, which is what ranks best.

**Passage selection, not truncation.** The index ranks *articles*; the answer
may be one paragraph near the bottom of a long one. `best_passages` scores
paragraphs by query-term overlap, keeps the lead paragraph in contention
(it defines the subject), then restores document order for readability.

## Defaults worth knowing

| flag | default | why |
|---|---|---|
| `--model` | `srini-coder:9b` | every `srini-*` tag bakes the lean operator profile into its SYSTEM block (1998 chars, ~500 tokens), which competes for attention with the retrieved sources — budget for it, or override the system prompt per request |
| `--top-k` | 4 | relevance falls off fast; more sources mostly buys latency |
| `--chars` | 1600 | per source; the whole prompt stays inside a 16k context |
| temperature | 0.2 | grounded extraction, not invention |

## Choosing archives

From <https://download.kiwix.org/zim/>, sizes as of 2026-11:

| archive | size | note |
|---|---|---|
| `wikipedia_en_all_maxi` | 119 G | everything, with images |
| `wikipedia_en_all_nopic` | 49 G | everything, no images |
| `wikipedia_en_all_mini` | 13 G | lead sections only — best size/value for Q&A |
| `wikipedia_en_top_mini` | 283 M | most-read articles |
| topic subsets | 12 M – 2 G | `chemistry_mini` 22 M, `climate-change_mini` 12 M, `physics_mini` 51 M, `medicine_mini` 166 M, `computer_nopic` 493 M |

`E:` has ~1.8 TB free, so even `all_maxi` fits. For factual Q&A the `mini`
flavours are usually the better trade: lead sections answer most questions and
search stays fast.

Non-Wikipedia archives work identically — Stack Exchange, Gutenberg, DevDocs,
Wiktionary are all on the same server and all carry full-text indexes.

## Files

```
zimrag.py        library: search, extract, rerank, prompt, answer
ask_zim.py       CLI
testdata/        a 12 MB climate-change ZIM used to verify the pipeline;
                 searched only with --include-testdata, so it never
                 contaminates the real corpus in ../zims
```

## Licensing

ZIM content keeps its upstream licence — Wikipedia is CC BY-SA. Quoting with a
citation is exactly the attribution that licence expects, which is a second
reason to prefer retrieval over baking the text into model weights.
