from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─── Enums ───

class ProjectStatus(str, Enum):
    created = "created"
    sourcing = "sourcing"
    outlining = "outlining"
    styling = "styling"
    ready = "ready"
    generating = "generating"
    done = "done"
    failed = "failed"


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class StepStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


# ─── Slide Outline ───

class SlideOutline(BaseModel):
    id: int
    title: str = ""
    content: str = ""
    layout: str = "content-text"
    notes: str = ""


class ProjectOutline(BaseModel):
    slides: list[SlideOutline] = []
    confirmed: bool = False


# ─── Design / Style ───

class DesignColors(BaseModel):
    primary: str = "#2563EB"
    secondary: str = "#7C3AED"
    accent: str = "#F59E0B"
    background: str = "#FFFFFF"
    text: str = "#1F2937"


class DesignFonts(BaseModel):
    heading: str = "Inter"
    body: str = "Inter"


class DesignChoice(BaseModel):
    style_id: str = ""
    mode_id: str = "narrative"
    colors: DesignColors = Field(default_factory=DesignColors)
    fonts: DesignFonts = Field(default_factory=DesignFonts)
    confirmed: bool = False


# ─── Source Entry ───

class SourceEntry(BaseModel):
    filename: str
    original_name: str = ""
    converted: bool = False
    converted_path: str = ""
    file_type: str = ""


# ─── Project ───

class Project(BaseModel):
    id: str
    name: str
    format: str = "ppt169"
    status: ProjectStatus = ProjectStatus.created
    task_id: Optional[str] = None
    sources: list[SourceEntry] = []
    topic: str = ""
    outline: ProjectOutline = Field(default_factory=ProjectOutline)
    design: DesignChoice = Field(default_factory=DesignChoice)
    created_at: str = ""
    updated_at: str = ""

    def touch(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now


# ─── Task (stored on disk) ───

class TaskStep(BaseModel):
    model_config = {"use_enum_values": True}
    
    name: str
    status: StepStatus = StepStatus.pending
    detail: str = ""


class Task(BaseModel):
    model_config = {"use_enum_values": True}
    
    task_id: str
    project_id: str
    status: TaskStatus = TaskStatus.pending
    progress: float = 0.0
    current_step: str = ""
    steps: list[TaskStep] = []
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def touch(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now


# ─── API request / response models ───

class ProjectCreate(BaseModel):
    name: str
    format: str = "ppt169"


class OutlineGenerate(BaseModel):
    topic: str = ""
    source_text: str = ""


class OutlineUpdate(BaseModel):
    slides: list[SlideOutline]
    confirmed: bool = False


class StyleSelect(BaseModel):
    style_id: str
    mode_id: str = "narrative"
    colors: Optional[DesignColors] = None
    fonts: Optional[DesignFonts] = None


class GenerateRequest(BaseModel):
    pass


class SourceUrlInput(BaseModel):
    url: str


class TopicInput(BaseModel):
    topic: str


# ─── Visual Style (read-only) ───

class VisualStyle(BaseModel):
    id: str
    name: str
    name_cn: str
    character: str
    best_for: str
    paired_rendering: str = ""


STYLES_CATALOG: list[VisualStyle] = [
    VisualStyle(id="swiss-minimal", name="Swiss Minimal", name_cn="瑞士风格", character="网格锁定、锋利、大量留白、无装饰", best_for="高端咨询、建筑、排版主导", paired_rendering="minimalist-swiss"),
    VisualStyle(id="soft-rounded", name="Soft Rounded", name_cn="柔和圆角", character="圆角卡片、柔和阴影、亲切感", best_for="产品/SaaS、培训、消费品牌", paired_rendering="flat"),
    VisualStyle(id="glassmorphism", name="Glassmorphism", name_cn="毛玻璃", character="半透明玻璃面板、渐变光效、浮动层次", best_for="现代SaaS、金融科技、AI演示", paired_rendering="glassmorphism"),
    VisualStyle(id="dark-tech", name="Dark Tech", name_cn="暗色科技", character="暗色画布、发光强调、几何精确", best_for="科技、AI、数据产品发布", paired_rendering="digital-dashboard"),
    VisualStyle(id="blueprint", name="Blueprint", name_cn="蓝图", character="原理图线条、暗色图纸、等轴测、标注", best_for="技术简报、架构、工程", paired_rendering="blueprint"),
    VisualStyle(id="editorial", name="Editorial", name_cn="杂志风格", character="杂志层级、分隔线/栏、衬线/无衬线搭配", best_for="金融、新闻、分析、解说", paired_rendering="editorial"),
    VisualStyle(id="photo-editorial", name="Photo Editorial", name_cn="摄影杂志", character="全出血摄影主导、文字点睛", best_for="建筑、设计、时尚、文化", paired_rendering="corporate-photo"),
    VisualStyle(id="data-journalism", name="Data Journalism", name_cn="数据新闻", character="多栏微图表、侧边栏、数据来源行、密集", best_for="金融、市场报告、研究、数据报表", paired_rendering="editorial"),
    VisualStyle(id="brutalist", name="Brutalist", name_cn="粗野主义", character="新闻纸密度、线框盒子、原始结构、扁平", best_for="年报、研究摘要、宣言", paired_rendering="screen-print"),
    VisualStyle(id="memphis", name="Memphis", name_cn="孟菲斯", character="撞色色块、几何纸屑、粗轮廓", best_for="节日、消费品牌、青年、发布造势", paired_rendering="flat"),
    VisualStyle(id="zine", name="Zine", name_cn="Zine风格", character="Riso套印偏差、半色调、有限调色板、印刷质感", best_for="文化、设计讲座、独立品牌", paired_rendering="screen-print"),
    VisualStyle(id="vintage-poster", name="Vintage Poster", name_cn="复古海报", character="世纪中期扁平色块、半色调、复古几何温暖感", best_for="传统、酒店、文化、周年纪念", paired_rendering="vintage-poster"),
    VisualStyle(id="paper-cut", name="Paper Cut", name_cn="剪纸风格", character="分层剪纸、柔和层间阴影、触感", best_for="文化/民俗、儿童、节日、可持续发展", paired_rendering="paper-cut"),
    VisualStyle(id="sketch-notes", name="Sketch Notes", name_cn="涂鸦笔记", character="暖色纸面、涂鸦线条、柔和粉彩", best_for="教育、培训、入门、知识分享", paired_rendering="sketch-notes"),
    VisualStyle(id="ink-notes", name="Ink Notes", name_cn="墨水笔记", character="浅色底色、黑色手墨、稀疏语义强调色", best_for="方法论、前后对比、宣言", paired_rendering="ink-notes"),
    VisualStyle(id="chalkboard", name="Chalkboard", name_cn="黑板风格", character="暗色石板、粉笔笔触、粉彩强调", best_for="教学、教程、课堂、学术", paired_rendering="chalkboard"),
    VisualStyle(id="ink-wash", name="Ink Wash", name_cn="水墨风格", character="宣纸留白、笔触痕迹、朱红印章、静", best_for="文化、哲学、传统、新中式", paired_rendering="ink-notes"),
]


# ─── Canvas Format ───

CANVAS_FORMATS: dict[str, str] = {
    "ppt169": "PPT 16:9 (标准)",
    "ppt43": "PPT 4:3",
    "xhs": "小红书图文",
    "story": "故事/竖版",
}
