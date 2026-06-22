import sys, os, time, subprocess, json, re, shutil, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from service.config import settings

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PARALLEL = 3  # 3 pages at a time

client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url, timeout=settings.llm_timeout)
proj_dir = Path("ppt-master/projects/campus-ai")

# Read project data
meta = json.loads(proj_dir.joinpath(".ppt_service.json").read_text("utf-8"))
slides = meta["outline"]["slides"]
design = meta["design"]
colors = design["colors"]
fonts = design["fonts"]

print(f"Project: {meta['name']}, {len(slides)} slides, style={design['style_id']}")
print(f"Colors: primary={colors['primary']}, bg={colors['background']}, text={colors['text']}")
print(f"Fonts: heading={fonts['heading']}, body={fonts['body']}")

svg_dir = proj_dir / "svg_output"
svg_dir.mkdir(parents=True, exist_ok=True)

# Check which pages already exist
existing = set()
for f in svg_dir.glob("page_*.svg"):
    existing.add(int(f.stem.split("_")[1]))
print(f"Existing pages: {sorted(existing) if existing else 'none'}")

def gen_page(slide):
    pid = slide["id"]
    if pid in existing:
        print(f"  P{pid:2d}: skip (already generated)")
        return pid, True
    
    c = colors; f = fonts
    sp = ("You are a PPT slide designer. Generate a complete SVG slide.\n"
          f"Page {pid}: {slide['title']}\n"
          f"Layout: {slide['layout']}\n"
          f"Content: {slide['content']}\n"
          f"Colors: primary={c['primary']}, secondary={c['secondary']}, accent={c['accent']}, bg={c['background']}, text={c['text']}\n"
          f"Fonts: title={f['heading']}, body={f['body']}\n"
          "Canvas: 1920x1080 (PPT 16:9)\n"
          "Output ONLY valid SVG code, no markdown fences, no explanations.\n"
          "Use viewBox='0 0 1920 1080', xmlns='http://www.w3.org/2000/svg'.\n"
          "Include proper layout, background, title, and content. Use the specified colors and fonts.")
    
    try:
        r = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": sp},
                {"role": "user", "content": f"Generate slide {pid}: {slide['title']}"}
            ],
            max_tokens=6144, temperature=0.7
        )
        content = r.choices[0].message.content or ""
        
        # Extract SVG
        m = re.search(r"<svg[\s\S]*?</svg>", content, re.IGNORECASE)
        svg = m.group() if m else ""
        if not svg:
            print(f"  P{pid:2d}: FAIL - empty SVG content")
            return pid, False
        
        svg_path = svg_dir / f"page_{pid:02d}.svg"
        svg_path.write_text(svg, encoding="utf-8")
        print(f"  P{pid:2d}: OK ({len(svg)} bytes) - {slide['title'][:30]}")
        return pid, True
    except Exception as e:
        print(f"  P{pid:2d}: FAIL - {str(e)[:100]}")
        return pid, False

# Generate in parallel batches
pending = [s for s in slides if s["id"] not in existing]
print(f"\nGenerating {len(pending)} pages (parallel={PARALLEL})...")
t0 = time.time()
success = 0; failed = 0

for i in range(0, len(pending), PARALLEL):
    batch = pending[i:i+PARALLEL]
    with ThreadPoolExecutor(max_workers=PARALLEL) as executor:
        futures = {executor.submit(gen_page, s): s for s in batch}
        for future in as_completed(futures):
            pid, ok = future.result()
            if ok: success += 1
            else: failed += 1

elapsed = time.time() - t0
print(f"\nDone in {elapsed:.0f}s: {success} ok, {failed} failed")

# After generation, run export
if success > 0:
    print("\nRunning post-processing pipeline...")
    sdir = str(Path("ppt-master/skills/ppt-master/scripts"))
    
    for step, cmd in [
        ("total_md_split", [sys.executable, f"{sdir}/total_md_split.py", str(proj_dir)]),
        ("finalize_svg", [sys.executable, f"{sdir}/finalize_svg.py", str(proj_dir)]),
        ("svg_to_pptx", [sys.executable, f"{sdir}/svg_to_pptx.py", str(proj_dir)]),
    ]:
        print(f"  {step}...", end=" ", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=os.getcwd())
        if r.returncode == 0:
            print("OK")
        else:
            print(f"FAIL: {r.stderr[:200]}")
    
    # Check exports
    exports_dir = proj_dir / "exports"
    ppts = sorted(exports_dir.glob("*.pptx")) if exports_dir.exists() else []
    if ppts:
        print(f"\n>>> PPTX generated: {ppts[-1]}")
        print(f"    Size: {ppts[-1].stat().st_size} bytes")
    else:
        print("\n>>> No PPTX found in exports/")
else:
    print("\nNo pages generated, skipping export")