const API = "";
let currentProject = null;
let currentTaskId = null;
let pollTimer = null;

// Helpers
async function api(method, path, body) {
    const opts = { method, headers: {} };
    if (body instanceof FormData) {
        opts.body = body;
    } else if (body) {
        opts.headers["Content-Type"] = "application/json";
        opts.body = JSON.stringify(body);
    }
    const r = await fetch(API + "/api" + path, opts);
    if (!r.ok) {
        const err = await r.text().catch(() => r.statusText);
        throw new Error(err.slice(0, 200));
    }
    const text = await r.text();
    return text ? JSON.parse(text) : {};
}

function show(id) { document.querySelectorAll(".page").forEach(p => p.classList.remove("active")); document.getElementById(id).classList.add("active"); }

// Pages
async function showHome() {
    show("page-home");
    const list = document.getElementById("project-list");
    list.innerHTML = '<div class="loading">加载中...</div>';
    try {
        const projects = await api("GET", "/projects");
        if (projects.length === 0) {
            list.innerHTML = '<div class="empty-state">暂无项目，创建一个开始吧</div>';
        } else {
            list.innerHTML = projects.map(p =>
                `<div class="project-card" onclick="loadProject('${p.id}')">
                  <div class="project-name">${p.name}</div>
                  <div class="project-meta">${p.status} · ${p.format}</div>
                  <div class="project-date">${new Date(p.updated_at || p.created_at).toLocaleString("zh-CN")}</div>
                </div>`
            ).join("");
        }
    } catch (e) { list.innerHTML = `<div class="error">加载失败: ${e.message}</div>`; }
}

async function createProject() {
    const name = document.getElementById("project-name").value.trim();
    if (!name) return alert("请输入项目名称");
    try {
        const p = await api("POST", "/projects", { name, format: "ppt169" });
        currentProject = p;
        showContentInput();
    } catch (e) { alert("创建失败: " + e.message); }
}

async function loadProject(id) {
    try {
        currentProject = await api("GET", `/projects/${id}`);
        if (currentProject.status === "generating") {
            showProgress();
        } else if (currentProject.status === "styling" || currentProject.status === "ready") {
            showConfirmation();
        } else if (currentProject.status === "outlining") {
            showOutlineEditor();
        } else {
            showContentInput();
        }
    } catch (e) { alert("加载失败: " + e.message); }
}

// Content Input
function showContentInput() {
    show("page-input");
    document.getElementById("current-project").textContent = `项目: ${currentProject.name}`;
}

async function setTopic() {
    const topic = document.getElementById("topic-input").value.trim();
    if (!topic) return alert("请输入主题描述");
    try {
        await api("PUT", `/projects/${currentProject.id}/topic`, { topic });
        currentProject.topic = topic;
        alert("主题已设置");
    } catch (e) { alert("设置失败: " + e.message); }
}

async function uploadFiles() {
    const files = document.getElementById("file-input").files;
    if (!files.length) return alert("请选择文件");
    const fd = new FormData();
    for (const f of files) fd.append("files", f);
    try {
        await api("POST", `/projects/${currentProject.id}/sources`, fd);
        currentProject.status = "sourcing";
        alert("文件上传成功");
    } catch (e) { alert("上传失败: " + e.message); }
}

async function genOutline() {
    if (!currentProject.topic && !currentProject.sources?.length) {
        alert("请先输入主题或上传源文件");
        return;
    }
    document.getElementById("gen-outline-btn").disabled = true;
    document.getElementById("gen-outline-btn").textContent = "生成中...";
    try {
        const r = await api("POST", `/projects/${currentProject.id}/outline`, {
            llm_api_key: "sk-Xxpqt3QblxHu5Mz7anpiUEBSM1ME04umGTMizDs4ky7MFyzTymYnQzWieKYzCJjV",
            llm_model: "qwen3.7-plus",
            llm_base_url: "https://opencode.ai/zen/go/v1"
        });
        currentProject.outline = r;
        showOutlineEditor();
    } catch (e) {
        alert("生成失败: " + e.message);
        document.getElementById("gen-outline-btn").disabled = false;
        document.getElementById("gen-outline-btn").textContent = "AI 生成大纲";
    }
}

// Outline Editor
function showOutlineEditor() {
    show("page-outline");
    renderOutline();
}

function renderOutline() {
    const slides = currentProject.outline?.slides || [];
    const container = document.getElementById("outline-editor");
    container.innerHTML = slides.map((s, i) =>
        `<div class="slide-card" data-idx="${i}">
          <div class="slide-handle">☰</div>
          <div class="slide-num">${s.id}</div>
          <div class="slide-fields">
            <input value="${s.title}" onchange="updateSlide(${i},'title',this.value)" placeholder="标题"/>
            <textarea rows="2" onchange="updateSlide(${i},'content',this.value)" placeholder="内容要点">${s.content}</textarea>
            <select onchange="updateSlide(${i},'layout',this.value)">
              ${["cover","content-text","content-image","comparison","chart","timeline","list","ending"].map(l =>
                `<option ${s.layout===l?"selected":""}>${l}</option>`
              ).join("")}
            </select>
          </div>
          <button class="btn-icon" onclick="delSlide(${i})" title="删除">✕</button>
        </div>`
    ).join("");
}

function updateSlide(idx, field, val) {
    currentProject.outline.slides[idx][field] = val;
}

function addSlide() {
    currentProject.outline.slides.push({
        id: currentProject.outline.slides.length + 1,
        title: "新页面", content: "", layout: "content-text", notes: ""
    });
    renderOutline();
}

function delSlide(idx) {
    currentProject.outline.slides.splice(idx, 1);
    currentProject.outline.slides.forEach((s, i) => s.id = i + 1);
    renderOutline();
}

async function confirmOutline() {
    try {
        const r = await api("PUT", `/projects/${currentProject.id}/outline`, {
            slides: currentProject.outline.slides,
            confirmed: true
        });
        currentProject.outline = r;
        showStyleSelector();
    } catch (e) { alert("保存失败: " + e.message); }
}

// Style Selector
async function showStyleSelector() {
    show("page-style");
    document.getElementById("current-project").textContent = `项目: ${currentProject.name}`;
    try {
        const styles = await api("GET", "/styles");
        const grid = document.getElementById("style-grid");
        grid.innerHTML = styles.map(s =>
            `<div class="style-card" onclick="selectStyle('${s.id}')" id="style-${s.id}">
              <div class="style-name">${s.id}</div>
              <div class="style-name-cn">${s.name_cn}</div>
              <div class="style-desc">${s.character}</div>
            </div>`
        ).join("");
    } catch (e) { alert("加载风格失败: " + e.message); }
}

async function selectStyle(id) {
    document.querySelectorAll(".style-card").forEach(c => c.classList.remove("selected"));
    document.getElementById("style-" + id).classList.add("selected");
    document.getElementById("style-id").value = id;
    document.getElementById("select-style-btn").disabled = false;
}

async function confirmStyle() {
    const styleId = document.getElementById("style-id").value;
    if (!styleId) return alert("请选择一个视觉风格");
    try {
        await api("POST", `/projects/${currentProject.id}/style`, { style_id: styleId, mode_id: "narrative" });
        showConfirmation();
    } catch (e) { alert("保存失败: " + e.message); }
}

// Confirmation
async function showConfirmation() {
    show("page-confirm");
    document.getElementById("current-project").textContent = `项目: ${currentProject.name}`;
    try {
        const preview = await api("GET", `/projects/${currentProject.id}/design-preview`);
        document.getElementById("preview-info").innerHTML =
            `<div class="preview-row"><span>页数</span><span>${preview.page_count}</span></div>
             <div class="preview-row"><span>风格</span><span>${preview.style_id}</span></div>
             <div class="preview-row"><span>格式</span><span>${preview.format}</span></div>
             <div class="preview-row"><span>主色</span><span style="color:${preview.colors.primary}">${preview.colors.primary}</span></div>
             <div class="preview-row"><span>标题字体</span><span>${preview.fonts.heading}</span></div>`;
    } catch (e) { document.getElementById("preview-info").textContent = "加载失败"; }
}

async function submitGeneration() {
    document.getElementById("generate-btn").disabled = true;
    document.getElementById("generate-btn").textContent = "提交中...";
    try {
        const r = await api("POST", `/projects/${currentProject.id}/generate`, {
            llm_api_key: "sk-Xxpqt3QblxHu5Mz7anpiUEBSM1ME04umGTMizDs4ky7MFyzTymYnQzWieKYzCJjV",
            llm_model: "qwen3.7-plus",
            llm_base_url: "https://opencode.ai/zen/go/v1"
        });
        currentTaskId = r.task_id;
        currentProject.status = "generating";
        showProgress();
    } catch (e) {
        alert("提交失败: " + e.message);
        document.getElementById("generate-btn").disabled = false;
        document.getElementById("generate-btn").textContent = "开始生成 PPT";
    }
}

// Progress
function showProgress() {
    show("page-progress");
    document.getElementById("current-project").textContent = `项目: ${currentProject.name}`;
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(pollTask, 3000);
    pollTask();
}

async function pollTask() {
    if (!currentTaskId) return;
    try {
        const task = await api("GET", `/tasks/${currentTaskId}`);
        const progress = Math.round((task.progress || 0) * 100);
        document.getElementById("progress-bar").style.width = progress + "%";
        document.getElementById("progress-text").textContent = `${progress}% - ${task.current_step || "处理中..."}`;
        const list = document.getElementById("step-list");
        list.innerHTML = (task.steps || []).map(s =>
            `<div class="step-item ${s.status}">${s.status === "running" ? "▶" : s.status === "completed" ? "✓" : s.status === "failed" ? "✕" : "○"} ${s.name} ${s.detail ? "- " + s.detail : ""}</div>`
        ).join("");
        if (task.status === "completed") {
            clearInterval(pollTimer);
            document.getElementById("progress-text").textContent = "✅ 生成完成!";
            if (task.result?.export_path) {
                document.getElementById("download-area").innerHTML =
                    `<a href="${API}/api${task.result.export_path}" class="btn primary" download>📥 下载 PPTX</a>
                     <button class="btn" onclick="showHome()">返回首页</button>`;
            }
        } else if (task.status === "failed") {
            clearInterval(pollTimer);
            document.getElementById("progress-text").textContent = "❌ 生成失败: " + (task.error || "未知错误");
        }
    } catch (e) { /* retry */ }
}

// Init
showHome();