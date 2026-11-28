# profile — what the local models know about you

`teacher_pipeline` teaches the Student *skills*. This directory teaches every
local model the *facts* about its operator and this machine.

```
USER_PROFILE.md           the facts. Single source of truth. Edit this.
MODEL_ROLES.md            what each srini-* model is FOR, and how the proxy
                          router picks one. Measured speeds and swap costs.
build_persona_models.py   profile -> SYSTEM block -> the srini-* tags (in place)
build/Modelfile.{4b,9b,35b}   generated; do not edit by hand
```

## Use

```bash
python profile/build_persona_models.py            # (re)build all three tags
python profile/build_persona_models.py --show      # see what the model sees
python profile/build_persona_models.py --model 9b  # just one

# Then talk to a tag that already carries the profile:
python ask_local_llm.py --model srini-coder:9b "How much VRAM can I spend?"

# Or inject the profile into a tag that does not - e.g. a fresh student export:
python ask_local_llm.py --persona --model qwen3.5-student:v2 "..."

cclocal srini-coder:9b      # a whole Claude Code session that knows you
```

Derived tags cost no extra disk: Ollama reuses the base model's blobs and stores
only the new Modelfile. Rebuilding is ~2 seconds per tag.

## Why facts are prompted and not trained

| | facts (`profile/`) | skills + style (`teacher_pipeline/`) |
|---|---|---|
| lives in | SYSTEM block | LoRA adapter weights |
| correcting it | edit a file, rebuild, ~2 s | retrain, or roll back the adapter |
| when wrong | model is immediately right | model argues with you until retrained |
| costs | ~1.7k tokens of context per session | 0 tokens, but VRAM and hours |

Hardware, model tags, project state and hyperparameters all change. A fact baked
into a 4B model's weights can't be edited, and the model will contradict it
whenever the prompt pulls the other way. So: facts here, skills there.

The ~1.7k-token cost is real but small against `srini-coder:9b`'s context, and it is
prompt-cached across turns within a session.

## Keeping it honest

Entries carry `[verified]` (observed on this machine) or `[inferred]` (deduced
from config or code style — worth confirming). Both markers are stripped before
the model sees them: they cost tokens and invite a small model to hedge.

The profile duplicates some values from `curriculum.yaml` so the model quotes
real hyperparameters instead of improvising them. When you change
`curriculum.yaml`'s `training:` block, update the profile's
"hyperparameters actually configured right now" section and rebuild — otherwise
the models will confidently quote stale numbers.
