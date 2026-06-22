import os, sys
from pathlib import Path

class Settings:
    def __init__(self):
        import os
        import sys
        # Try to load .env file
        _env_paths = [
            Path(__file__).resolve().parent.parent / ".env",
            Path(__file__).resolve().parent.parent / ".env.local",
        ]
        for _env_p in _env_paths:
            if _env_p.exists():
                for _line in _env_p.read_text("utf-8").splitlines():
                    _line = _line.strip()
                    if _line and not _line.startswith("#") and "=" in _line:
                        _k, _v = _line.split("=", 1)
                        _k, _v = _k.strip(), _v.strip().strip("'\"")
                        if _k not in os.environ:
                            os.environ[_k] = _v
                break
        service_dir = Path(__file__).resolve().parent
        repo_root = service_dir.parent
        self.ppt_master_dir = os.environ.get("PPT_SERVICE_PPT_MASTER_DIR", str(repo_root / "ppt-master"))
        self.scripts_dir = os.environ.get("PPT_SERVICE_SCRIPTS_DIR", str(Path(self.ppt_master_dir) / "skills" / "ppt-master" / "scripts"))
        self.projects_dir = os.environ.get("PPT_SERVICE_PROJECTS_DIR", str(Path(self.ppt_master_dir) / "projects"))
        self.tasks_dir = os.environ.get("PPT_SERVICE_TASKS_DIR", str(service_dir / "tasks"))
        self.host = os.environ.get("PPT_SERVICE_HOST", "0.0.0.0")
        self.port = int(os.environ.get("PPT_SERVICE_PORT", "8765"))
        # LLM config (required)
        self.llm_api_key = os.environ.get("PPT_SERVICE_LLM_API_KEY")
        self.llm_model = os.environ.get("PPT_SERVICE_LLM_MODEL")
        self.llm_base_url = os.environ.get("PPT_SERVICE_LLM_BASE_URL")
        self.llm_timeout = int(os.environ.get("PPT_SERVICE_LLM_TIMEOUT", "120"))
        
        if not self.llm_api_key:
            raise ValueError("PPT_SERVICE_LLM_API_KEY is required. Set it in .env or environment variables.")
        if not self.llm_model:
            raise ValueError("PPT_SERVICE_LLM_MODEL is required. Set it in .env or environment variables.")
        if not self.llm_base_url:
            raise ValueError("PPT_SERVICE_LLM_BASE_URL is required. Set it in .env or environment variables.")
        Path(self.projects_dir).mkdir(parents=True, exist_ok=True)
        Path(self.tasks_dir).mkdir(parents=True, exist_ok=True)

    def python_cmd(self):
        return sys.executable

settings = Settings()
