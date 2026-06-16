import sys, os, json, re, subprocess
from pathlib import Path
from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LLM_KEY = "sk-Xxpqt3QblxHu5Mz7anpiUEBSM1ME04umGTMizDs4ky7MFyzTymYnQzWieKYzCJjV"
LLM_URL = "https://opencode.ai/zen/go/v1"
MODEL = "qwen3.7-plus"

proj_dir = Path("ppt-master/projects/campus-ai")
svg_dir = proj_dir / "svg_output"
svg_dir.mkdir(parents=True, exist_ok=True)

meta = json.loads(proj_dir.joinpath(".ppt_service.json").read_text("utf-8"))
slides = meta["outline"]["slides"]
c = meta["design"]["colors"]
f = meta["design"]["fonts"]
total = len(slides)

# Check existing
existing = {}
for fp in sorted(svg_dir.glob("page_*.svg")):
    pid = int(fp.stem.split("_")[1])
    existing[pid] = fp

# Find first missing page
missing = [s for s in slides if s["id"] not in existing]
if not missing:
    print(f"All {total} pages generated! Run export to get PPTX.")
    sys.exit(0)

slide = missing[0]
pid = slide["id"]
prev_pid = pid - 1
print(f"\n=== Page {pid}/{total}: {slide['title']} ===")
print(f"Layout: {slide['layout']}")
print(f"Previous pages available: {sorted(existing.keys())}")

# Build system prompt with visual context from previous page
base_prompt = (
    f"You are a PPT slide designer. Generate an SVG slide.\n"
    f"Canvas: 1920x1080 (PPT 16:9). Output ONLY valid SVG, no markdown.\n"
    f"Colors: primary={c['primary']}, secondary={c['secondary']}, accent={c['accent']}, bg={c['background']}, text={c['text']}\n"
    f"Fonts: title={f['heading']}, body={f['body']}\n"
)

# Include ALL previous SVGs as visual references for consistency
if existing:
    ref_names = sorted(existing.keys())
    base_prompt += (
        "\n=== PREVIOUS SLIDES (visual references, newest last) ===\n"
        "Below are ALL previously generated slides. Maintain CONSISTENT visual style:\n"
        "- Same background treatment (gradient, color, opacity, blob placement)\n"
        "- Same decorative elements (left stripe, gradient blobs, line separators)\n"
        "- Same typography hierarchy (title ~48px, subtitle ~28px, body ~20-22px)\n"
        "- Same card/panel styling (rounded rects, F8FAFC bg, E2E8F0 border, 12px radius)\n"
        "- Same color usage pattern (primary #2563EB for highlights, secondary #7C3AED for accents)\n"
    )
    for ref_pid in ref_names:
        svg_content = existing[ref_pid].read_text("utf-8")
        base_prompt += f"\n--- Page {ref_pid} SVG ---\n{svg_content}\n"

# Build page-specific content
user_prompt = (
    f"Generate slide {pid} of {total}.\n"
    f"Title: {slide['title']}\n"
    f"Layout type: {slide['layout']}\n"
    f"Content: {slide['content'][:500]}\n"
    f"Speaker notes: {slide['notes'][:200] if slide['notes'] else 'N/A'}\n"
)

client = OpenAI(api_key=LLM_KEY, base_url=LLM_URL, timeout=120)

try:
    r = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=6144,
        temperature=0.7,
    )
    content = r.choices[0].message.content or ""
    
    m = re.search(r"<svg[\s\S]*?</svg>", content, re.IGNORECASE)
    svg = m.group() if m else ""
    
    if svg:
        svg_path = svg_dir / f"page_{pid:02d}.svg"
        svg_path.write_text(svg, encoding="utf-8")
        print(f"  OK: {len(svg)} bytes -> {svg_path.name}")
    else:
        print(f"  FAIL: empty SVG response")
        sys.exit(1)
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Report progress
remaining = len([s for s in slides if s["id"] not in set(int(x.stem.split("_")[1]) for x in svg_dir.glob("page_*.svg"))])
print(f"\nProgress: {total - remaining}/{total} pages")
if remaining == 0:
    print(f"\n>>> All pages complete! Run:")
    print(f"    python ppt-master/skills/ppt-master/scripts/svg_to_pptx.py {proj_dir}")
else:
    print(f"Run again for next page (python service/next_page.py)")
