# Projects, repositories and shipping history

Companion to `USER_PROFILE.md`, baked into the `srini-*` tags by
`build_persona_models.py`. Facts live here rather than in LoRA weights because
three measured lessons showed that training at this scale moves style and
*reduces* factual density - see the note at the end.

`[verified]` read from GitHub or the working tree on 2026-11-24 ·
`[inferred]` deduced from naming or history.

---

## GitHub identity

- Account: **Srinivasan-78**. `gh` is authenticated with scopes
  `gist, read:org, repo, workflow`. `[verified]`
- **462 pull requests** authored in total. Of a 200-PR sample: **197 across 21
  of their own repositories**, and **3 to external projects** - one to
  `Danielskry/Awesome-RAG`, one each to `TensorBlock/awesome-mcp-servers` and
  `punkpeye/awesome-mcp-servers`. So the work is overwhelmingly on their own
  repos, with external contributions limited to list curation. `[verified]`

## repo2graph - the flagship

- Public, MIT, **9 stars**, primary language Python (plus Makefile, Dockerfile,
  TypeScript, JavaScript). `[verified]`
- Description: *"Give coding agents trustworthy, cited answers about your
  codebase. Code graph + MCP server, no LLM required."* `[verified]`
- **142 PRs** - 122 merged, 20 closed. The single largest body of work. `[verified]`
- **Two clones exist and they are not equivalent:** `[verified]`

  | path | version | HEAD | branch | python |
  |---|---|---|---|---|
  | `E:\Github\repo2graph` | **5.0.0** | `ab2e1598` 2026-11-23 | `fix/audit-round-7` | `>=3.11` |
  | `C:\Users\Srini\code\repo2graph` | 3.0.0 | `14364a9` 2026-10-12 | `develop` | `>=3.10` |

  **`E:\Github\repo2graph` is authoritative.** The `C:` clone is two major
  versions and about six weeks stale; never quote versions, flags, or the
  Python floor from it. Python 3.10 was dropped in PR #527, which cleared all
  31 Dependabot alerts.
- Package layout: a flat `repo2graph/` package - `answer.py`, `audit.py`,
  `autobuild.py`, `cache.py`, `chunks.py`, `cli.py`, `cli_embed.py`,
  `cli_inspect.py`, `cochange.py`, `config.py`, `derived.py`, `discovery.py`,
  `doctor.py`, `edgemeta.py`, `embed.py` and more. `[verified]`
- **102 test files** under `tests/`, with `conftest.py`, `fixtures/` and
  `golden/` directories - golden-file tests are part of the contract, so
  changing output format means updating goldens deliberately. `[verified]`
- Makefile is the entry point for everything: `install`, `lint`, `format`,
  `format-check`, `typecheck`, `test`, `test-serial`, `test-cov`, `clean`. `[verified]`
- **13 CI workflows**: `ci`, `codeql`, `compliance`, `dependabot-triage`,
  `dependency-audit`, `dependency-review`, `lockfile`, `perf`, `benchmark`,
  `examples`, `index-repo`, `prod-igy`. Supply chain and compliance are
  automated, not manual. `[verified]`
- Also ships as a GitHub Action (`action.yml`), an npm wrapper (`npm/`), editor
  integrations (`editors/`), and an MCP server manifest (`server.json`). `[verified]`

## Other active repositories

| repo | language | PRs | notes |
|---|---|---|---|
| `srinivasan-78.github.io` | TypeScript | 13 | Portfolio and systems-engineering workbench; MIT; React 19 / Tailwind 4 / ESLint 10 |
| `authormark-watch` | JavaScript | 3 | "Daily cross-repo authorship watermark monitor", 1 star, MIT |
| `highq-devops-kb` | Shell, PowerShell | - | **Private** DevOps knowledge base |
| `tokenmiser` | - | 1 | The token-reduction skill suite installed in this Claude Code |

Further own repos with merged PRs: `pi-image-tools`, `local-photo-browser`,
`minecraft-server-gitops`, `doc2md-action`, `cairn`, `azure-pipeline-trigger`,
`multi-ai-toolkit`, `vfactor-solutions-site`, `filescan-hub`,
`study-brainrot-generator`, `self-healing-deployment`, `browser-pdf-tools`,
`multicloud-free-tier`, `agentic-app-loop`, `wix-installer-template`. `[verified]`

The spread - Raspberry Pi imaging, GitOps for a Minecraft server, Azure
pipeline triggers, multicloud free tier, self-healing deployment - says the
interest is infrastructure and automation, not application UI. `[inferred]`

## How work is shipped

- **Conventional-commit PR titles with scopes**, and they read as sentences
  rather than labels: `fix(export): restrict the whole staged tree, not the
  manifest's list`, `perf(scroll): remove wasted backdrop blur`,
  `feat(examples): add Rails and Spring Framework to the gallery (#462)`. `[verified]`
- `feat!:` marks a breaking change - `feat!: clear all 31 Dependabot alerts
  (drops Python 3.10)`. `[verified]`
- **Audit rounds are a recurring unit of work**: numbered batches that fix a
  backlog and then fix what reviewing the batch itself uncovered - *"Land the
  audit-round-7 fixes, and fix the double close reviewing them found"*. Reviewing
  a fix batch is expected to produce more findings. `[verified]`
- A PR titled plainly `Develop` is a branch promotion (develop -> main), not a
  feature. `[verified]`
- Recurring themes across 2026: security hardening, clearing Dependabot and
  supply-chain alerts, explicit performance budgets, CodeQL findings, and CI
  reliability on Windows runners. `[verified]`
- Issues are referenced by number in titles and bodies (`(#462)`), so a change
  is expected to name what it closes. `[verified]`

## Working in these repos

- Verify with the Makefile before claiming done: `make lint`, `make typecheck`,
  `make test`. `make test-serial` exists for tests that cannot run in
  parallel - reach for it when a parallel run is flaky, not by default. `[verified]`
- Dependencies are locked with `uv` (`uv.lock`), and a `lockfile` workflow
  guards it, so a dependency change that skips the lock will fail CI. `[verified]`
- There is **no `CLAUDE.md` or `AGENTS.md`** in repo2graph, so none of these
  conventions are written down for an agent inside the repo itself - they have
  to be inferred from the Makefile, the workflows and the PR history. `[verified]`
- Licensing is REUSE-compliant (`REUSE.toml`, `LICENSES/`) and there is a
  `CITATION.cff`, so new files are expected to carry licence headers and the
  compliance workflow will say so if they do not. `[verified]`

## Attribution caveat

These are pull requests authored by the **Srinivasan-78 account**. Which of them
were Claude-assisted is not recorded anywhere I can read, so nothing here
attributes work to an assistant. No PR has been raised from this session.

## Why these facts are prompted, not trained

Three lessons were trained and graded on 2026-11-24. Every one improved
formatting and conciseness and *reduced* factual density: numbers stated fell
0.596 -> 0.42 and identifiers 0.308 -> 0.185 against base, under a rubric
specifically rewritten to weight numbers and identifiers at 80%. At 91 training
rows, rank 16, and 3-8 optimizer steps per lesson, LoRA learns phrasing, not
knowledge. So version numbers, paths, PR conventions and repo inventories belong
here - correctable in one edit and a two-second rebuild - and the weights get
procedure and style instead.
