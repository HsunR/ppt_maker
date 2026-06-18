# PPT Master Service — 项目架构与思路

## 项目定位

将 **PPT Master**（一个 AI agent 驱动的原生 PPTX 生成工作流）包装为可独立调用的 Web 服务 + 前端应用，实现"输入文档/主题 → 自动生成可编辑 PPTX"的全流程自动化。

## 整体架构

```
用户 (浏览器)                        服务器 (本地)
┌──────────┐     HTTP      ┌──────────────────────┐
│ Vue 3    │ ──────────→  │ FastAPI Backend       │
│ SPA      │ ←──────────  │  ├─ routers/          │
│ (5173)   │     JSON     │  ├─ utils/llm.py      │──→ OpenAI API
└──────────┘              │  └─ utils/scripts.py  │──→ PPT-Master 脚本
                          └──────────────────────┘
                                   │
                          ┌────────┴────────┐
                          │ PPT-Master Engine│
                          │ (python-pptx,    │
                          │  svg_to_pptx...) │
                          └─────────────────┘
```

- **前端**：Vue 3 + Vite，Hash 路由，6 个步骤页面
- **后端**：FastAPI，提供 REST API，异步任务管理
- **引擎**：PPT Master (`ppt-master/`) 的 Python 脚本，通过 subprocess 调用
- **LLM**：OpenAI 兼容 API，通过流式传输调用推理模型

## 用户流程

```
首页 → 创建项目 → 输入内容 → AI 生成大纲 → 编辑大纲
→ 选择视觉风格 → 确认 → 提交生成 → 实时进度 → 下载 PPTX
```

每个步骤有独立的 Vue 视图，状态通过 reactive store 共享。

## 生成管线

全流程分三步执行：

| 步骤 | 组件 | 说明 |
|------|------|------|
| 大纲生成 | LLM (Strategist 角色) | 分析源内容 → 产出结构化 JSON 大纲 |
| SVG 生成 | LLM (Executor 角色) | 逐页调用 LLM 生成 SVG（含全部前页作为上下文） |
| PPTX 导出 | PPT-Master 脚本 | total_md_split → finalize_svg → svg_to_pptx |

生成通过后台线程异步执行，前端轮询 `/api/tasks/{id}` 获取进度。

## 关键设计决策

### 1. 串行 vs 并行

最初尝试并行生成 SVG（3 页一组），后改为**串行逐页生成**。每页生成时**注入全部已有页面的 SVG 代码**作为视觉参考上下文，确保风格一致性。代价是 prompt 随页数增长，LLM 处理时间递增。

### 2. 推理模型兼容

`deepseek-v4-flash` 是推理模型，与普通模型有三个关键差异：

| 问题 | 表现 | 修复 |
|------|------|------|
| `reasoning_content` 先于 `content` | 空响应 | `stream=True` 流式收集 |
| token 预算分配 | JSON 被截断 | `max_tokens=65536` |
| 字符串含真实换行符 | JSON 解析失败 | `try_parse_json()` 自动清洗 |

### 3. JSON 解析容错

`try_parse_json()` 处理顺序：

1. 直接解析（清洗控制字符后）
2. 提取 ```json ... ``` 代码块
3. 提取 `[...]` 区间
4. 修复未闭合的字符串和括号
5. 截断到最后一个完整 `}`

### 4. 任务状态管理

- 每个生成任务对应 `service/tasks/{task_id}.json`
- 磁盘持久化，API 重启后仍可查询进度
- 后台线程执行，浏览器刷新不中断

### 5. 路径编码

Windows 下中文项目名导致文件系统路径编码问题。修复：内部 ID 自动 sanitize 为 ASCII-only（`java入门` → `java___`），`name` 字段保留中文显示。

### 6. 超时处理

API 网关（Cloudflare）对非流式请求有 120 秒超时限制。解决方案：

- 所有 LLM 调用使用 `stream=True`，数据持续流动不触发超时
- OpenAI 客户端 `timeout=300`（5 分钟）
- shell 命令 `timeout_ms=420000`（7 分钟）

## 目录结构

```
ppt/
├── frontend-vue/           # 前端 SPA（Vue 3 + Vite）
│   ├── src/views/          # 6 个步骤视图
│   ├── src/api.js          # API 请求 + 共享状态
│   ├── src/router.js       # Hash 路由
│   └── dist/               # 构建产物
├── service/                # 后端（FastAPI）
│   ├── main.py
│   ├── routers/
│   │   ├── projects.py     # 20+ API 端点
│   │   └── styles.py       # 17 套视觉风格
│   ├── utils/
│   │   ├── llm.py          # LLM 调用（流式、JSON 容错）
│   │   ├── scripts.py      # PPT-Master 脚本包装
│   │   └── tasks.py        # 磁盘任务状态
│   └── tasks/              # 任务 JSON 存储
├── .env                    # LLM 配置
└── ppt-master/             # PPT-Master 引擎（只读）
```

## 当前状态

- 后端：全部 20+ API 端点通过测试
- 前端：完整 SPA（含 SVG 实时预览、只读回看）
- 全流程：文档转换 → 大纲生成 → SVG 生成 → PPTX 导出已跑通
- 已知限制：LLM 调用依赖第三方 API 可用性和响应速度