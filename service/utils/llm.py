"""LLM API client wrapper (OpenAI-compatible)."""
from __future__ import annotations
from typing import Optional
from openai import OpenAI, APITimeoutError
from service.config import settings

def get_client(api_key: str = "", base_url: str = "", timeout: Optional[int] = None) -> OpenAI:
    return OpenAI(
        api_key=api_key or settings.llm_api_key,
        base_url=base_url or settings.llm_base_url,
        timeout=timeout or settings.llm_timeout,
    )

def call_llm(
    system_prompt: str,
    user_message: str,
    model: str = "",
    api_key: str = "",
    base_url: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> tuple[bool, str]:
    """Call OpenAI-compatible LLM. Returns (success, content_or_error)."""
    client = get_client(api_key, base_url)
    model = model or settings.llm_model
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        return True, content
    except APITimeoutError:
        return False, "LLM请求超时，请检查模型响应速度或增加超时时间"
    except Exception as e:
        return False, f"LLM调用失败: {e}"