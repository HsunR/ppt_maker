# PPT Generator

AI-powered PPT generation system with Vue frontend and FastAPI backend.

## Project Structure

```
ppt/
├── frontend-vue/           # Vue 3 + Vite frontend
├── service/                # FastAPI backend
│   ├── main.py             # App entry point
│   ├── config.py           # Configuration
│   ├── routers/            # API endpoints
│   ├── schemas/            # Pydantic models
│   └── utils/              # Utilities & LLM client
├── ppt-master/             # PPT generation engine
└── .env                    # Environment variables
```

## Quick Start

### Backend

```bash
# Install dependencies
pip install fastapi uvicorn python-dotenv httpx

# Configure .env
cp .env.example .env
# Edit .env with your LLM API key

# Start server
python -m uvicorn service.main:app --reload
```

### Frontend

```bash
cd frontend-vue
npm install
npm run dev
```

Access at http://localhost:5173

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PPT_SERVICE_LLM_API_KEY` | LLM API key |
| `PPT_SERVICE_LLM_BASE_URL` | LLM API base URL |
| `PPT_SERVICE_LLM_MODEL` | Model name |
| `PPT_SERVICE_LLM_TIMEOUT` | Request timeout (seconds) |

## API Endpoints

- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project status
- `POST /api/projects/{id}/generate` - Generate PPT
- `GET /api/styles` - List available styles

## Tech Stack

- **Frontend**: Vue 3, Vite, Vue Router
- **Backend**: FastAPI, Pydantic
- **LLM**: OpenAI-compatible API
