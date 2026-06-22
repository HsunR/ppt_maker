import os, json
from openai import OpenAI
from service.config import settings

client = OpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    timeout=settings.llm_timeout,
)
r = client.chat.completions.create(
    model=settings.llm_model,
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