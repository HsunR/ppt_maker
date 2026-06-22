import sys, os, json, re
from pathlib import Path
from openai import OpenAI
from service.config import settings

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
proj_name = sys.argv[1] if len(sys.argv) > 1 else "ma-test"

proj_dir = Path("ppt-master/projects") / proj_name
for d in sorted(Path("ppt-master/projects").iterdir()):
    if d.is_dir() and d.name.startswith(proj_name): proj_dir = d; break

meta = json.loads((proj_dir / ".ppt_service.json").read_text("utf-8"))
slides = meta["outline"]["slides"]
c = meta["design"]["colors"]; f = meta["design"]["fonts"]
total = len(slides)
svg_dir = proj_dir / "svg_output"; svg_dir.mkdir(parents=True, exist_ok=True)
existing = {int(x.stem.split("_")[1]): x for x in svg_dir.glob("page_*.svg")}
missing = [s for s in slides if s["id"] not in existing]
if not missing: print(f"All {total} done!"); sys.exit(0)

slide = missing[0]; pid = slide["id"]
print(f"P{pid}/{total}: {slide['title']}")

# Build prompt with ALL previous SVGs as context
prompt = (
    f"PPT slide designer. Generate SVG slide {pid} of {total}.\n"
    f"1920x1080. Output ONLY SVG, no markdown.\n"
    f"Colors: primary={c['primary']} secondary={c['secondary']} accent={c['accent']} bg={c['background']} text={c['text']}\n"
    f"Fonts: heading={f['heading']} body={f['body']}\n"
    f"Layout: {slide['layout']}\nTitle: {slide['title']}\nContent: {slide['content'][:500]}\n"
)

# Include ALL previous SVGs
if existing:
    prompt += "\n=== ALL PREVIOUS SLIDES (maintain exact style) ===\n"
    for rid in sorted(existing):
        svg_c = existing[rid].read_text("utf-8")
        prompt += f"\n--- Page {rid} ---\n{svg_c}\n"

client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url, timeout=settings.llm_timeout)
r = client.chat.completions.create(model=settings.llm_model,
    messages=[{"role":"system","content":prompt},{"role":"user","content":f"SVG slide {pid}"}],
    max_tokens=32768, temperature=0.7, stream=True)

content = ""; reason_chunks = 0; finish = "unknown"
for chunk in r:
    ch = chunk.choices[0]
    if ch.delta and ch.delta.reasoning_content: reason_chunks += 1
    if ch.delta and ch.delta.content: content += ch.delta.content
    if ch.finish_reason: finish = ch.finish_reason
print(f"  reasoning: {reason_chunks} chunks, finish: {finish}, response: {len(content)} chars")

svg = (re.search(r"<svg[\s\S]*?</svg>", content, re.IGNORECASE) or type("",(),{"group":lambda *a:""})()).group()
if svg:
    (svg_dir / f"page_{pid:02d}.svg").write_text(svg, encoding="utf-8")
    remaining = len([s for s in slides if s["id"] not in set(int(x.stem.split("_")[1]) for x in svg_dir.glob("page_*.svg"))])
    print(f"OK ({len(svg)}b), {total-remaining}/{total}, {remaining} remaining")
else:
    print(f"FAIL: no <svg> tag, content={len(content)} chars, preview={content[:300]}")
    if content: print(f"  preview: {content[:200]}")