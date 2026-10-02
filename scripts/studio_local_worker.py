#!/usr/bin/env python3
"""Run a bounded local Studio draft and independent gpt-6.1-sol/high audit."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import html
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from china_tech_x_radar.studio_flow import (
    LOCAL_MODEL, AUDIT_MODEL, AUDIT_EFFORT, accept, audit_prompt, digest,
    local_prompt, validate_draft, validate_request, write_json,
)


def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise ValueError("JSON object required")
    return obj


def local_chat(messages, key_file):
    key = Path(key_file).read_text().strip()
    body = {"model": LOCAL_MODEL, "messages": messages, "stream": True,
            "stream_options": {"include_usage": True}, "max_tokens": 1600, "temperature": 0}
    req = urllib.request.Request("http://127.0.0.1:18080/v1/chat/completions",
                                 data=json.dumps(body, ensure_ascii=False).encode(),
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    start = time.monotonic(); text = ""; usage = {}; actual = set(); finish = None
    with opener.open(req, timeout=180) as response:
        for line in response:
            line = line.decode().strip()
            if not line.startswith("data:"):
                continue
            raw = line[5:].strip()
            if raw == "[DONE]":
                break
            value = json.loads(raw)
            if value.get("model"):
                actual.add(value["model"])
            if value.get("usage"):
                usage = value["usage"]
            for choice in value.get("choices", []):
                text += (choice.get("delta") or {}).get("content") or ""
                finish = choice.get("finish_reason") or finish
    if actual and actual != {LOCAL_MODEL}:
        raise ValueError("local model identity drift: " + str(actual))
    if finish != "stop":
        raise ValueError("local generation incomplete: " + str(finish))
    return {"text": text, "model": LOCAL_MODEL, "actual_models": sorted(actual),
            "usage": usage, "seconds": round(time.monotonic() - start, 3)}


def render(req, draft, out, easel_root):
    escaped = html.escape
    facts = req["inputs"]["facts"]
    sources = " · ".join(dict.fromkeys(f["source_label"] for f in facts))
    points = "".join('<section class="box"><span>0' + str(i + 1) + '</span><p>' + escaped(p["text"]) + '</p></section>'
                     for i, p in enumerate(draft["points"]))
    css = '''*{box-sizing:border-box}html,body{margin:0;width:1600px;height:900px;background:#fafaf8;color:#242424;font-family:"PingFang SC",sans-serif}main{padding:30px 64px}header{font:22px/1.2 monospace;letter-spacing:2px;color:#002fa7}h1{font-size:54px;line-height:1.1;font-weight:500;margin:18px 0 10px}.subtitle{font-size:25px;color:#707070;margin-bottom:22px}.points{display:grid;gap:12px}section{display:flex;gap:28px;align-items:center;height:160px;border-top:1px solid #d0d0cc;padding:15px 12px}section span{font-size:38px;color:#002fa7}section p{margin:0;font-size:40px;line-height:1.4}footer{font-size:22px;line-height:1.4;color:#606060;margin-top:22px;white-space:pre-line}.box{min-width:0}'''
    if len(draft["points"]) == 2:
        css += "section{height:245px}section p{font-size:50px;line-height:1.35}.points{gap:0}"
    page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><style>' + css + '</style><main><header>AI实战 · @KennyChinaTech</header><h1 class="box">' + escaped(draft["title"]) + '</h1><div class="subtitle box">' + escaped(req["inputs"].get("subtitle", "事实卡片 · 待人工发布")) + '</div><div class="points">' + points + '</div><footer class="box">来源：' + escaped(sources) + '\n' + escaped(req["inputs"].get("scope_note", "")) + '</footer></main></html>'
    path = out / "card.html"; path.write_text(page)
    png = out / "card.png"
    cmd = [sys.executable, str(easel_root / "skills/shared/scripts/render_card.py"),
           "--html", str(path), "--out", str(png), "--full-page", "--width", "1600", "--height", "900", "--scale", "1"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    write_json(out / "render.json", {"exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    if result.returncode:
        raise RuntimeError("Easel render failed")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        pg = browser.new_page(viewport={"width": 1600, "height": 900})
        pg.goto(path.as_uri()); pg.evaluate("document.fonts.ready")
        dom = pg.evaluate("""()=>({width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,overflow:[...document.querySelectorAll('.box')].filter(e=>e.scrollWidth>e.clientWidth+1||e.getBoundingClientRect().bottom>900).map(e=>e.textContent)})""")
        browser.close()
    result = subprocess.run([sys.executable, str(easel_root / "skills/openclaw/card-design/scripts/card_audit.py"),
                             "audit", "-f", str(png), "--json"], capture_output=True, text=True, timeout=60)
    write_json(out / "layout.json", dom)
    write_json(out / "card-audit.json", {"exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    return png, {"layout": dom["width"] == 1600 and dom["height"] == 900 and not dom["overflow"],
                 "easel_card_audit": result.returncode == 0}


def gpt_audit(req, draft, checks, out, codex, image):
    raw = out / "gpt-verdict.json"
    if raw.exists():
        raise ValueError("audit destination already exists; use a fresh attempt directory")
    cmd = [str(codex), "exec", "--ignore-user-config", "--ignore-rules", "--ephemeral", "--skip-git-repo-check",
           "-s", "read-only", "-m", AUDIT_MODEL, "-c", 'model_reasoning_effort="high"', "-o", str(raw)]
    if image:
        cmd += ["--image", str(image)]
    cmd.append("-")
    start = time.monotonic()
    proc = subprocess.run(cmd, input=audit_prompt(req, draft, checks), capture_output=True, text=True, timeout=240, cwd=out)
    (out / "gpt-trace.log").write_text(proc.stderr)
    if proc.returncode or not raw.exists():
        raise RuntimeError("GPT audit failed; no model fallback")
    if "model: " + AUDIT_MODEL not in proc.stderr or "reasoning effort: high" not in proc.stderr:
        raise ValueError("GPT invocation identity not confirmed")
    return {"model": AUDIT_MODEL, "effort": AUDIT_EFFORT,
            "request_sha256": req["request_sha256"], "draft_sha256": digest(draft),
            "artifact_sha256": hashlib.sha256(image.read_bytes()).hexdigest() if image else None,
            "seconds": round(time.monotonic() - start, 3), "verdict": parse_json(raw.read_text())}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--request", required=True); p.add_argument("--out", required=True)
    p.add_argument("--repair-from", help="one bounded repair of an independently rejected attempt")
    p.add_argument("--key-file", default="/Users/momentgrid/ModelServices/work/main.key")
    p.add_argument("--easel-root", default="/Users/momentgrid/easel-validation-20261002/source")
    p.add_argument("--codex", default="/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex")
    args = p.parse_args(); out = Path(args.out).resolve()
    if out.exists():
        raise ValueError("output already exists; do not replay an unknown attempt")
    out.mkdir(parents=True)
    req = json.loads(Path(args.request).read_text()); validate_request(req)
    write_json(out / "request.json", req)
    write_json(out / "method.json", {"worker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                    "contract_sha256": hashlib.sha256(Path(__file__).resolve().parents[1].joinpath("src/china_tech_x_radar/studio_flow.py").read_bytes()).hexdigest(),
                                    "prompt_sha256": hashlib.sha256(local_prompt(req).encode()).hexdigest()})
    feedback = None
    if args.repair_from:
        prior = Path(args.repair_from).resolve()
        if (prior / "repair-parent.json").exists():
            raise ValueError("repair budget exhausted")
        previous_req = json.loads((prior / "request.json").read_text())
        previous_audit = json.loads((prior / "audit.json").read_text())
        previous_draft = json.loads((prior / "draft.json").read_text())
        validate_draft(previous_req, previous_draft)
        if previous_req != req or previous_audit.get("request_sha256") != req["request_sha256"] or previous_audit.get("draft_sha256") != digest(previous_draft):
            raise ValueError("repair feedback binding mismatch")
        if previous_audit.get("model") != AUDIT_MODEL or previous_audit.get("effort") != AUDIT_EFFORT or previous_audit.get("verdict", {}).get("decision") != "REJECT":
            raise ValueError("repair requires independent rejection")
        feedback = previous_audit["verdict"]
        write_json(out / "repair-parent.json", {"path": str(prior), "audit_sha256": digest(previous_audit), "round": 1})
    # Serializes this workflow only; existing model-service admission stays authoritative.
    with (out.parent / ".local-flow.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        messages = [{"role": "user", "content": local_prompt(req)}]; attempts = []
        if feedback:
            messages += [{"role": "assistant", "content": json.dumps(previous_draft, ensure_ascii=False)},
                         {"role": "user", "content": "独立审核未通过：" + json.dumps(feedback, ensure_ascii=False)
                          + "。修复问题后重新输出完整JSON。重新核对每个分组的样本数量和指标，不能把总体样本数量写成原创帖样本数量。保留未知与小样本限制，不修改原始数据。"}]
        for attempt in range(2):
            response = local_chat(messages, args.key_file); attempts.append(response)
            write_json(out / "local-attempts.json", attempts)
            try:
                draft = parse_json(response["text"]); validate_draft(req, draft); break
            except (ValueError, KeyError, TypeError) as exc:
                if attempt == 1:
                    raise
                messages += [{"role": "assistant", "content": response["text"]},
                             {"role": "user", "content": "格式验证失败：" + str(exc) + "。按原约定重新输出JSON。"}]
        write_json(out / "draft.json", draft)
        checks = {"schema": True}; image = None
        if req["kind"] == "card":
            image, layout = render(req, draft, out, Path(args.easel_root)); checks.update(layout)
        write_json(out / "checks.json", checks)
        if not all(v is True for v in checks.values()):
            write_json(out / "blocked.json", {"status": "BLOCKED_DETERMINISTIC_CHECK", "checks": checks})
            raise ValueError("repair deterministic layout before requesting GPT audit")
        audit = gpt_audit(req, draft, checks, out, Path(args.codex), image)
        write_json(out / "audit.json", audit)
        receipt = accept(req, draft, audit, checks)
        receipt["artifact_sha256"] = audit["artifact_sha256"]
        write_json(out / "accepted.json", receipt)
        print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
