"""Subprocess wrappers for ppt-master scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

from service.config import settings

PYTHON = settings.python_cmd()
SCRIPTS = settings.scripts_dir


def _run(cmd: list[str], cwd: Optional[str] = None, timeout: Optional[int] = 300) -> tuple[int, str, str]:
    """Run a command, return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd or settings.ppt_master_dir,
            timeout=timeout,
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


# ─── Project Management ───

def project_init(name: str, fmt: str = "ppt169", proj_dir: Optional[str] = None) -> tuple[bool, str]:
    """Initialize a new project. Returns (success, project_path_or_error)."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "project_manager.py"), "init", name, "--format", fmt]
    rc, out, err = _run(cmd)
    if rc != 0:
        return False, err or out
    # Extract project path from output ("Project created: <path>")
    for line in out.splitlines():
        line = line.strip()
        if "Project created:" in line:
            return True, line.split(":", 1)[1].strip()
        if "Project initialized:" in line:
            return True, line.split(":", 1)[1].strip()
    # Fallback: scan projects dir for the latest matching directory
    import re
    proj_dir_path = Path(settings.projects_dir)
    pattern = re.compile(rf"^{re.escape(name)}_.*")
    matches = []
    for d in proj_dir_path.iterdir():
        if d.is_dir() and pattern.match(d.name):
            matches.append((d.stat().st_mtime, d))
    if matches:
        matches.sort(reverse=True)
        return True, str(matches[0][1])
    return False, "Could not find created project directory"


def project_validate(project_path: str) -> tuple[bool, list[str], list[str]]:
    """Validate project structure. Returns (is_valid, errors, warnings)."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "project_manager.py"), "validate", project_path]
    rc, out, err = _run(cmd)
    errors = []
    warnings = []
    in_errors = False
    in_warnings = False
    for line in out.splitlines():
        if "[ERROR]" in line:
            in_errors = True
            in_warnings = False
            continue
        if "[WARN]" in line:
            in_warnings = True
            in_errors = False
            continue
        if in_errors and line.strip().startswith("-"):
            errors.append(line.strip().lstrip("- "))
        if in_warnings and line.strip().startswith("-"):
            warnings.append(line.strip().lstrip("- "))
    is_valid = rc == 0 and "[OK]" in out
    return is_valid, errors, warnings


def project_info(project_path: str) -> dict:
    """Get project info as dict."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "project_manager.py"), "info", project_path]
    rc, out, err = _run(cmd)
    info = {}
    for line in out.splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("=") and not line.startswith("Project"):
            key, val = line.split(":", 1)
            info[key.strip()] = val.strip()
    return {"raw": out, "parsed": info} if info else {"raw": out, "error": err}


def project_import_sources(project_path: str, files: list[str]) -> tuple[bool, str]:
    """Import source files into a project."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "project_manager.py"), "import-sources", project_path, *files, "--move"]
    rc, out, err = _run(cmd)
    return rc == 0, out or err


# ─── Document Conversion ───

def convert_pdf(file_path: str) -> tuple[bool, str]:
    """Convert PDF to Markdown."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "source_to_md" / "pdf_to_md.py"), file_path]
    rc, out, err = _run(cmd, timeout=120)
    return rc == 0, out or err


def convert_docx(file_path: str) -> tuple[bool, str]:
    """Convert DOCX to Markdown."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "source_to_md" / "doc_to_md.py"), file_path]
    rc, out, err = _run(cmd, timeout=120)
    return rc == 0, out or err


def convert_excel(file_path: str) -> tuple[bool, str]:
    """Convert Excel to Markdown."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "source_to_md" / "excel_to_md.py"), file_path]
    rc, out, err = _run(cmd, timeout=120)
    return rc == 0, out or err


def convert_pptx(file_path: str) -> tuple[bool, str]:
    """Convert PPTX to Markdown."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "source_to_md" / "ppt_to_md.py"), file_path]
    rc, out, err = _run(cmd, timeout=120)
    return rc == 0, out or err


def convert_url(url: str) -> tuple[bool, str]:
    """Convert URL to Markdown."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "source_to_md" / "web_to_md.py"), url]
    rc, out, err = _run(cmd, timeout=120)
    return rc == 0, out or err


CONVERTERS = {
    ".pdf": convert_pdf,
    ".docx": convert_docx,
    ".doc": convert_docx,
    ".xlsx": convert_excel,
    ".xlsm": convert_excel,
    ".pptx": convert_pptx,
    ".ppt": convert_pptx,
}


def convert_file(file_path: str) -> tuple[bool, str]:
    """Auto-detect file type and convert."""
    ext = Path(file_path).suffix.lower()
    converter = CONVERTERS.get(ext)
    if not converter:
        return False, f"Unsupported file type: {ext}"
    return converter(file_path)


# ─── Post-processing Pipeline ───

def run_total_md_split(project_path: str) -> tuple[bool, str]:
    """Step 7.1: Split speaker notes."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "total_md_split.py"), project_path]
    rc, out, err = _run(cmd, timeout=120)
    return rc == 0, out or err


def run_finalize_svg(project_path: str) -> tuple[bool, str]:
    """Step 7.2: Finalize SVG (icons, images, text flatten, etc.)."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "finalize_svg.py"), project_path]
    rc, out, err = _run(cmd, timeout=300)
    return rc == 0, out or err


def run_svg_to_pptx(project_path: str, animation: str = "fade", auto_advance: Optional[int] = None) -> tuple[bool, str]:
    """Step 7.3: Export PPTX."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "svg_to_pptx.py"), project_path]
    if animation:
        cmd += ["-t", animation]
    if auto_advance:
        cmd += ["--auto-advance", str(auto_advance)]
    rc, out, err = _run(cmd, timeout=600)
    return rc == 0, out or err


def run_image_gen(manifest_path: str) -> tuple[bool, str]:
    """AI image generation via manifest."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "image_gen.py"), "--manifest", manifest_path]
    rc, out, err = _run(cmd, timeout=300)
    return rc == 0, out or err


def run_image_search(project_path: str, prompt: str) -> tuple[bool, str]:
    """Web image search."""
    cmd = [PYTHON, str(Path(SCRIPTS) / "image_search.py"), project_path, "--prompt", prompt]
    rc, out, err = _run(cmd, timeout=120)
    return rc == 0, out or err
