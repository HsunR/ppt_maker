# Repository Guidelines

## Project Structure & Module Organization

```
ppt/
├── frontend-vue/           # Vue 3 + Vite frontend (SPA)
│   └── src/views/          # 6 route views: Home, Input, Outline, Style, Confirm, Progress
├── service/                # FastAPI backend
│   ├── main.py             # App entry, CORS, static mount
│   ├── config.py           # Settings from .env / env vars
│   ├── routers/            # API endpoints (projects, styles)
│   ├── schemas/models.py   # Pydantic models
│   ├── utils/              # Script wrappers, task state, LLM client
│   └── orchestrator/       # Reserved for full pipeline orchestration
├── .env                    # LLM API key, base URL, model, timeout
└── ppt-master/             # Upstream PPT-Master engine (read-only submodule)
```

## Build, Test, and Development Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server (port 5173, proxies `/api` to backend) |
| `npm run build` | Production build to `dist/` (served by FastAPI at `/`) |
| `python -m uvicorn service.main:app` | Start FastAPI backend (port 8765) |
| `python service/next_page.py <project>` | Generate one SVG page (serial, with full context) |

Set `PPT_SERVICE_LLM_*` env vars or use the `.env` file before starting the backend.

## Coding Style & Naming Conventions

- **Python**: 4-space indent. Functions/variables use `lowercase_with_underscores`. Constants use `UPPER_CASE`.
- **Vue/JavaScript**: 2-space indent. Methods/variables use `camelCase`. Components use `PascalCase`. Single File Components with `<template>`, `<script>`, `<style scoped>`.
- **API routes**: `snake_case` for path segments, e.g. `/api/projects/{id}/design-preview`.
- **LLM prompts**: Stored inline as triple-quoted Python strings. Keep system prompts concise and imperative.

## Testing Guidelines

- No formal test framework is configured. Tests run ad hoc via Python scripts in `service/*.py`.
- API endpoints can be tested manually with `httpx` or `Invoke-RestMethod`.
- Run `python service/final_demo.py` (when present) for a quick endpoint health check.
- Add test cases in project validation scripts when introducing new endpoints.

## Commit & Pull Request Guidelines

Commits follow the `type: message` convention from the existing history:

- `feat:` — new feature (frontend view, API endpoint, generation capability)
- `fix:` — bug fix (path encoding, JSON parsing, timeout, indentation)
- `chore:` — maintenance (.gitignore, cleanup, config)

PRs should include a change summary, any API contract changes, and manual testing evidence (screenshots or command output).

## Security & Configuration

- LLM credentials go in `.env` (git-ignored). Never commit an API key directly.
- `.env` is read automatically by `config.py` as a fallback when env vars are not set.
- FastAPI CORS is open (`allow_origins=["*"]`) — restrict in production deployments.
- The `frontend-vue/dist/` build output is served statically; keep it in sync with `npm run build`.