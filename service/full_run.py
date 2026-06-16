import sys, os, time, subprocess, httpx, shutil, json, re
from pathlib import Path

os.environ.update({
    "PPT_SERVICE_LLM_BASE_URL": "https://opencode.ai/zen/go/v1",
    "PPT_SERVICE_LLM_API_KEY": "sk-Xxpqt3QblxHu5Mz7anpiUEBSM1ME04umGTMizDs4ky7MFyzTymYnQzWieKYzCJjV",
    "PPT_SERVICE_LLM_MODEL": "qwen3.7-plus",
})
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Cfg
LLM = {"llm_api_key": "sk-Xxpqt3QblxHu5Mz7anpiUEBSM1ME04umGTMizDs4ky7MFyzTymYnQzWieKYzCJjV",
       "llm_model": "qwen3.7-plus", "llm_base_url": "https://opencode.ai/zen/go/v1"}
BASE = "http://localhost:8765"

print("[0] Converting document...")
docx = Path(r"D:\0Document\school work\AI\人工智能大作业\提交\第四组_基于情感解答领域微调模型与RAG回复增强校园AI问答系统（项目分工文档）.docx")
temp_md = Path("_temp_campus.md")
r = subprocess.run([sys.executable, "ppt-master/skills/ppt-master/scripts/source_to_md/doc_to_md.py",
    str(docx), "-o", str(temp_md)], capture_output=True, text=True, timeout=30)
for f in Path(".").glob("_temp*"): temp_md = f; break
topic_text = temp_md.read_text(encoding="utf-8")[:12000]
print(f"  Converted: {len(topic_text)} chars")

# Clean
for d in Path("ppt-master/projects").iterdir():
    if d.is_dir() and "campus" in d.name.lower(): shutil.rmtree(d)

print("[1] Starting server...")
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "service.main:app", "--host", "0.0.0.0", "--port", "8765"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.getcwd())
time.sleep(8)

ok = fail = 0
def t(n, fn):
    global ok, fail
    try:
        r = fn()
        if 200 <= r.status_code < 300: ok += 1; print(f"  [OK] {n}"); return r
        else: fail += 1; print(f"  [FAIL] {n} s={r.status_code}"); return r
    except Exception as e: fail += 1; print(f"  [FAIL] {n} {type(e).__name__}"); return None

try:
    r0 = t("Create project", lambda: httpx.post(BASE+"/api/projects", json={"name":"campus-ai","format":"ppt169"}, timeout=10))
    pid = r0.json()["id"] if r0 else "campus-ai"
    t("Set topic", lambda: httpx.put(BASE+f"/api/projects/{pid}/topic", json={"topic":topic_text}, timeout=10))

    print("  >>> LLM outline...")
    r = t("Outline", lambda: httpx.post(BASE+f"/api/projects/{pid}/outline", json=LLM, timeout=120))
    slides = r.json().get("slides", []) if r else []
    for s in slides: print(f"     P{s['id']:2d}: {s['title']} [{s['layout']}]")
    if not slides: raise SystemExit("No slides")

    t("Confirm", lambda: httpx.put(BASE+f"/api/projects/{pid}/outline", json={"slides":slides,"confirmed":True}, timeout=10))
    t("Style", lambda: httpx.post(BASE+f"/api/projects/{pid}/style", json={"style_id":"dark-tech","mode_id":"narrative"}, timeout=10))

    print("  >>> Generation...")
    r = t("Submit", lambda: httpx.post(BASE+f"/api/projects/{pid}/generate", json=LLM, timeout=10))
    tid = r.json().get("task_id","") if r else ""
    if not tid: raise SystemExit("No task")

    max_wait, waited = 900, 0
    while waited < max_wait:
        time.sleep(15); waited += 15
        try:
            tr = httpx.get(BASE+f"/api/tasks/{tid}", timeout=10)
            td = tr.json()
            st = td.get("status","?"); pct = int(td.get("progress",0)*100)
            print(f"  [{waited}s] {pct}% {td.get('current_step','')} [{st}]")
            for s in td.get("steps",[]):
                if s.get("status") in ("running","completed","failed"):
                    print(f"    [{s['status']}] {s['name']} {s.get('detail','')[:120]}")
            if st in ("completed","failed"):
                print(f"\n  FINAL: {st}")
                if td.get("result"): print(f"  Result: {json.dumps(td['result'], ensure_ascii=False)}")
                if td.get("error"): print(f"  Error: {td['error']}")
                break
        except Exception as e: print(f"  Poll: {e}")

    # Check exports
    pdir = None
    for d in Path("ppt-master/projects").iterdir():
        if d.is_dir() and "campus" in d.name.lower(): pdir = d; break
    if pdir:
        ppts = sorted(pdir.glob("exports/*.pptx"))
        svgs = list(pdir.glob("svg_output/*.svg"))
        print(f"\n  Project: {pdir}")
        print(f"  SVGs: {len(svgs)} files")
        if ppts: print(f"  PPTX: {ppts[-1]} ({ppts[-1].stat().st_size} bytes)")
        else: print("  No PPTX yet")
    else:
        print("  Project dir not found!")

finally:
    proc.terminate(); proc.wait(2)

print(f"\nDone. ok={ok} fail={fail}")
temp_md.unlink(missing_ok=True)