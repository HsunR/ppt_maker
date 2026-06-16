import os, json
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["PPT_SERVICE_LLM_API_KEY"],
    base_url=os.environ["PPT_SERVICE_LLM_BASE_URL"],
)
r = client.chat.completions.create(
    model="qwen3.7-plus",
    messages=[
        {"role": "system", "content": "You are a PPT designer. Generate a simple SVG slide. Output ONLY SVG code, no markdown fences."},
        {"role": "user", "content": 'Generate a cover page SVG with title "AI Campus Assistant" and subtitle "Project Overview". viewBox="0 0 1920 1080". Use colors: primary=#2563EB, bg=#FFFFFF, text=#1F2937.'}
    ],
    max_tokens=2048,
    temperature=0.7
)
c = r.choices[0].message.content
if c:
    print(f"SVG content: {len(c)} chars")
    print(c[:600])
else:
    print("EMPTY content!")
    print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2)[:1000])