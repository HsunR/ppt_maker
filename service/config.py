import os, sys
from pathlib import Path

class Settings:
    def __init__(self):
        service_dir = Path(__file__).resolve().parent
        repo_root = service_dir.parent
        self.ppt_master_dir = os.environ.get("PPT_SERVICE_PPT_MASTER_DIR", str(repo_root / "ppt-master"))
        self.scripts_dir = os.environ.get("PPT_SERVICE_SCRIPTS_DIR", str(Path(self.ppt_master_dir) / "skills" / "ppt-master" / "scripts"))
        self.projects_dir = os.environ.get("PPT_SERVICE_PROJECTS_DIR", str(Path(self.ppt_master_dir) / "projects"))
        self.tasks_dir = os.environ.get("PPT_SERVICE_TASKS_DIR", str(service_dir / "tasks"))
        self.host = os.environ.get("PPT_SERVICE_HOST", "0.0.0.0")
        self.port = int(os.environ.get("PPT_SERVICE_PORT", "8765"))
        # LLM defaults
        self.llm_api_key = os.environ.get("PPT_SERVICE_LLM_API_KEY", "")
        self.llm_model = os.environ.get("PPT_SERVICE_LLM_MODEL", "qwen3.7-plus")
        self.llm_base_url = os.environ.get("PPT_SERVICE_LLM_BASE_URL", "https://opencode.ai/zen/go/v1")
        self.llm_timeout = int(os.environ.get("PPT_SERVICE_LLM_TIMEOUT", "120"))
        Path(self.projects_dir).mkdir(parents=True, exist_ok=True)
        Path(self.tasks_dir).mkdir(parents=True, exist_ok=True)

    def python_cmd(self):
        return sys.executable

settings = Settings()