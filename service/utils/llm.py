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
    max_tokens: int = 65536,
    stream: bool = True,  # default to streaming for reasoning model safety
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
            stream=stream,
        )
        content = ""
        for chunk in response:
            ch = chunk.choices[0]
            if ch.delta and ch.delta.content:
                content += ch.delta.content
        return True, content
    except APITimeoutError:
        return False, "LLM请求超时"
    except Exception as e:
        return False, f"LLM调用失败: {e}"

def call_llm_nonstream(
    system_prompt: str,
    user_message: str,
    model: str = "",
    api_key: str = "",
    base_url: str = "",
    temperature: float = 0.7,
    max_tokens: int = 65536,
) -> tuple[bool, str]:
    """Non-streaming fallback for models that don't support streaming."""
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
        if not content and hasattr(response.choices[0].message, 'reasoning_content'):
            content = response.choices[0].message.reasoning_content or ""
        return True, content
    except APITimeoutError:
        return False, "LLM请求超时"
    except Exception as e:
        return False, f"LLM调用失败: {e}"

def try_parse_json(text: str):
    """Try to extract and parse JSON from LLM response. Returns parsed data or None.
    Handles markdown code blocks, unterminated strings, and mixed content."""
    import json as _json
    import re
    # Sanitize: control chars that break JSON (deepseek outputs literal 0x0A inside strings)
    text = text.replace(chr(10), chr(32)).replace(chr(13), chr(32))
    # Try 1: direct parse
    try:
        return _json.loads(text)
    except _json.JSONDecodeError:
        pass
    # Try 2: extract content between ```json ... ```
    m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if m:
        try:
            return _json.loads(m.group(1))
        except _json.JSONDecodeError:
            pass
    # Try 3: extract content between [ and ]
    m = re.search(r'\[([\s\S]*?)\]', text)
    if m:
        try:
            return _json.loads('[' + m.group(1) + ']')
        except _json.JSONDecodeError:
            pass
    # Try 4: fix unterminated strings
    m = re.search(r'\[[\s\S]*?(?:\]|$)', text)
    if m:
        candidate = m.group(0)
        # Add missing closing bracket if missing
        if not candidate.endswith(']'):
            candidate += ']'
        # Fix unterminated strings (odd number of quotes before closing)
        lines = candidate.split('\n')
        for li, line in enumerate(lines):
            in_str = False
            fix_pos = -1
            for ci, ch in enumerate(line):
                if ch == '"' and (ci == 0 or line[ci-1] != '\\'):
                    in_str = not in_str
            if in_str:
                # String never closed on this line
                line += '"'
                lines[li] = line
        candidate = '\n'.join(lines)
        try:
            return _json.loads(candidate)
        except _json.JSONDecodeError:
            pass
    # Try 5: truncated JSON - find last complete object, close it, and close the array
    try:
        t = text.strip()
        # Find last complete {object}
        last_close = t.rfind('}')
        if last_close > t.rfind('['):
            t = t[:last_close+1] + ']'
            return _json.loads(t)
    except:
        pass
    return None
