import sys, os, time, subprocess, httpx, shutil, json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:8765"

# Step 0: Convert document to MD in a temp location first
docx = Path(r"D:\0Document\school work\AI\人工智能大作业\提交\第四组_基于情感解答领域微调模型与RAG回复增强校园AI问答系统（项目分工文档）.docx")
if not docx.exists():
    print(f"Document not found: {docx}")
    sys.exit(1)

temp_md = Path("ppt-master/projects/_temp_campus.md")
print(f"[0] Converting DOCX to MD...")
r = subprocess.run([sys.executable, "ppt-master/skills/ppt-master/scripts/source_to_md/doc_to_md.py", str(docx), "-o", str(temp_md)],
    capture_output=True, text=True, timeout=30)
print(f"  stdout: {r.stdout.strip()}")
if r.returncode != 0:
    print(f"  stderr: {r.stderr}")
    sys.exit(1)

# Find the actual MD output (doc_to_md might add its own extension)
for candidate in [temp_md, temp_md.with_suffix(".docx.md"), temp_md.with_suffix(".txt")]:
    if candidate.exists():
        temp_md = candidate
        break
if not temp_md.exists():
    # Look for any MD file
    for f in Path("ppt-master/projects").glob("_temp*"):
        temp_md = f; break

topic_text = temp_md.read_text(encoding="utf-8")[:12000]
print(f"  MD size: {len(topic_text)} chars")
print(f"  Preview: {topic_text[:200].replace(chr(10), ' ')}...")

# Clean up old project
shutil.rmtree("ppt-master/projects/campus-ai", ignore_errors=True)

print("[1] Starting server...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "service.main:app", "--host", "0.0.0.0", "--port", "8765"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.getcwd()
)
time.sleep(8)

ok, fail = 0, 0
def test(n, fn):
    global ok, fail
    try:
        r = fn()
        if 200 <= r.status_code < 300:
            ok += 1; print(f"  [OK] {n}"); return r
        else:
            fail += 1; print(f"  [FAIL] {n} status={r.status_code} body={r.text[:200]}"); return r
    except Exception as e:
        fail += 1; print(f"  [FAIL] {n} {type(e).__name__}: {str(e)[:100]}"); return None

try:
    r = test("Create project", lambda: httpx.post(BASE+"/api/projects", json={"name":"campus-ai","format":"ppt169"}, timeout=10))
    if not r or r.status_code >= 300: raise SystemExit()

    r = test("Set topic", lambda: httpx.put(BASE+"/api/projects/campus-ai/topic", json={"topic": topic_text}, timeout=10))

    print("  >>> AI generating outline...")
    r = test("Generate outline", lambda: httpx.post(BASE+"/api/projects/campus-ai/outline", json={}, timeout=120))
    slides = r.json().get("slides", []) if r else []
    for s in slides:
        print(f"     P{s['id']:2d}: {s['title']} [{s['layout']}]")
    print(f"  Total: {len(slides)} slides")
    if not slides: raise SystemExit("No slides")

    test("Confirm outline", lambda: httpx.put(BASE+"/api/projects/campus-ai/outline", json={"slides":slides,"confirmed":True}, timeout=10))
    test("Select style", lambda: httpx.post(BASE+"/api/projects/campus-ai/style", json={"style_id":"dark-tech","mode_id":"narrative"}, timeout=10))

    print("  >>> Submitting generation...")
    r = test("Submit generate", lambda: httpx.post(BASE+"/api/projects/campus-ai/generate", json={}, timeout=10))
    tid = r.json().get("task_id","") if r else ""
    if not tid: raise SystemExit("No task ID")

    print(f"  Task ID: {tid}")
    print("  >>> Polling (max 10 min)...")
    max_wait, waited = 600, 0
    while waited < max_wait:
        time.sleep(15); waited += 15
        try:
            tr = httpx.get(BASE+f"/api/tasks/{tid}", timeout=10)
            td = tr.json()
            st = td.get("status","?"); pct = int(td.get("progress",0)*100)
            print(f"  [{waited}s] {pct}% - {td.get('current_step','')} [{st}]")
            for s in td.get("steps",[]):
                if s.get("status") in ("running","completed","failed"):
                    print(f"    [{s['status']}] {s['name']} {s.get('detail','')}")
            if st in ("completed","failed"):
                print(f"\n  FINAL: {st}")
                if td.get("result"): print(f"  Result: {json.dumps(td['result'], ensure_ascii=False)}")
                if td.get("error"): print(f"  Error: {td['error']}")
                break
        except Exception as e: print(f"  Poll error: {e}"); break

    # Check results
    exp = Path("ppt-master/projects/campus-ai/exports")
    ppts = sorted(exp.glob("*.pptx")) if exp.exists() else []
    if ppts: print(f"\n  PPTX: {ppts[-1]} ({ppts[-1].stat().st_size} bytes)")
    else: print("\n  No PPTX generated")
    svgs = list(Path("ppt-master/projects/campus-ai/svg_output").glob("*.svg"))
    print(f"  SVGs: {len(svgs)} files")

finally:
    proc.terminate(); proc.wait(2)

print(f"\nDone. ok={ok} fail={fail}")