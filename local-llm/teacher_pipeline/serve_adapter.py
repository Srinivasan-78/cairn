#!/usr/bin/env python3
"""Minimal Ollama-compatible HTTP server for grading a PEFT LoRA adapter in WSL2.

Exposes:
  GET  /api/version  -> {"version": "serve_adapter-0.1"}
  POST /api/chat     -> {"message": {"content": ..., "thinking": ...}, ...}

Switches between the trained adapter (`--tag`, e.g. student:trained) and the
unmodified base (`--base-tag`, e.g. student:base) using PEFT's
`disable_adapter()` context manager so both share one 4-bit model load.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--adapter", required=True, help="Path to PEFT adapter directory.")
    p.add_argument("--port", type=int, default=11436)
    p.add_argument("--tag", default="student:trained")
    p.add_argument("--base-tag", default="student:base")
    p.add_argument("--max-seq-length", type=int, default=2048)
    args = p.parse_args()

    import torch
    from peft import PeftConfig, PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    peft_cfg = PeftConfig.from_pretrained(args.adapter)
    base_id = peft_cfg.base_model_name_or_path
    bnb_cfg = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_id)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_id, quantization_config=bnb_cfg, device_map="auto"
    )
    model = PeftModel.from_pretrained(base_model, args.adapter)
    model.eval()

    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, code: int, payload: dict) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if self.path.startswith("/api/version"):
                self._send_json(200, {"version": "serve_adapter-0.1"})
            else:
                self._send_json(404, {"error": "not found"})

        def do_POST(self) -> None:
            if not self.path.startswith("/api/chat"):
                self._send_json(404, {"error": "not found"})
                return
            try:
                length = max(0, int(self.headers.get("Content-Length", 0)))
                req = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as e:
                self._send_json(400, {"error": f"invalid request: {e}"})
                return

            messages = req.get("messages", [])
            opts = req.get("options") or {}
            max_new = int(opts.get("num_predict", 512))
            temp = float(opts.get("temperature", 0.2))
            use_base = req.get("model") == args.base_tag

            try:
                prompt = tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                inputs = tokenizer(
                    prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=args.max_seq_length,
                ).to(model.device)
                t0 = time.monotonic()
                gen_kwargs: dict = dict(
                    **inputs,
                    max_new_tokens=max_new,
                    do_sample=temp > 0,
                )
                if temp > 0:
                    gen_kwargs["temperature"] = temp
                with torch.inference_mode():
                    if use_base:
                        with model.disable_adapter():
                            out = model.generate(**gen_kwargs)
                    else:
                        out = model.generate(**gen_kwargs)

                new_ids = out[0][inputs["input_ids"].shape[1] :]
                decoded = tokenizer.decode(new_ids, skip_special_tokens=True)
                raw = decoded if isinstance(decoded, str) else "".join(decoded)
                m = THINK_RE.search(raw)
                thinking = m.group(1).strip() if m else ""
                content = THINK_RE.sub("", raw).strip() if m else raw.strip()
                dt_ns = int((time.monotonic() - t0) * 1e9)
                self._send_json(
                    200,
                    {
                        "model": req.get("model", args.tag),
                        "message": {"role": "assistant", "content": content, "thinking": thinking},
                        "prompt_eval_count": int(inputs["input_ids"].shape[1]),
                        "eval_count": len(new_ids),
                        "eval_duration": dt_ns,
                        "done_reason": "length" if len(new_ids) >= max_new else "stop",
                    },
                )
            except Exception as e:  # noqa: BLE001 - HTTP handler boundary
                self._send_json(500, {"error": f"generation failed: {e}"})

        def log_message(self, format: str, *args: object) -> None:
            pass

    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
