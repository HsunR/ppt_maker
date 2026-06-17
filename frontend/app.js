const { createApp } = Vue;

createApp({
  data() {
    return {
      page: 'home',
      steps: ['内容输入', 'AI 大纲', '视觉风格', '确认生成', '生成进度'],
      step: 0,
      loading: false, error: '',
      projects: [],
      newName: '',
      currentProject: null,

      topicText: '', urlText: '', uploadMsg: '', genLoading: false,
      slides: [], layouts: ['cover','content-text','content-image','comparison','chart','timeline','list','ending'],
      styles: [], styleId: '', styleName: '',
      designColors: {}, designFonts: {},

      taskId: '', progressPct: 0, progressText: '准备中...',
      taskSteps: [], taskDone: false, taskError: '', downloadUrl: '',
      pollTimer: null,
    };
  },

  async mounted() {
    await this.loadProjects();
  },

  watch: {
    page(val) {
      const idx = { home: 0, input: 1, outline: 2, style: 3, confirm: 4, progress: 5 }[val] || 0;
      this.step = idx;
    }
  },

  methods: {
    fmtDate(d) { return d ? new Date(d).toLocaleString('zh-CN') : ''; },

    async api(method, path, body) {
      const opts = { method, headers: {} };
      if (body instanceof FormData) opts.body = body;
      else if (body) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
      const r = await fetch('/api' + path, opts);
      if (!r.ok) { const t = await r.text().catch(() => r.statusText); throw new Error(t.slice(0, 300)); }
      return r.status === 204 ? null : r.json();
    },

    // ─── Home ───
    async loadProjects() {
      this.loading = true;
      try { this.projects = await this.api('GET', '/projects'); } catch (e) { this.error = e.message; }
      finally { this.loading = false; }
    },

    async createProject() {
      if (!this.newName.trim()) return;
      try {
        const p = await this.api('POST', '/projects', { name: this.newName, format: 'ppt169' });
        this.currentProject = p;
        this.newName = '';
        this.page = 'input';
        await this.loadProjects();
      } catch (e) { this.error = e.message; }
    },

    async loadProject(p) {
      this.currentProject = p;
      if (p.status === 'outlining') { this.page = 'outline'; this.slides = p.outline?.slides || []; }
      else if (p.status === 'ready') { this.page = 'confirm'; }
      else if (p.status === 'generating') { this.taskId = ''; this.page = 'progress'; this.startPolling(); }
      else { this.page = 'input'; }
    },

    goHome() { this.stopPolling(); this.page = 'home'; this.loadProjects(); this.taskId = ''; },

    // ─── Input ───
    async saveTopic() {
      if (!this.topicText.trim()) return;
      if (!this.currentProject) return;
      await this.api('PUT', `/projects/${this.currentProject.id}/topic`, { topic: this.topicText });
      this.uploadMsg = '主题已保存';
    },

    async uploadFiles(e) {
      const files = e.target?.files || e;
      if (!files?.length) return;
      const fd = new FormData();
      for (const f of files) fd.append('files', f);
      try {
        const r = await this.api('POST', `/projects/${this.currentProject.id}/sources`, fd);
        this.uploadMsg = `上传 ${r.sources.length} 个文件成功`;
      } catch (e) { this.uploadMsg = '上传失败: ' + e.message; }
    },

    onDrop(e) { this.uploadFiles(e.dataTransfer.files); },

    async importUrl() {
      if (!this.urlText.trim()) return;
      await this.api('POST', `/projects/${this.currentProject.id}/sources/url`, { url: this.urlText });
      this.uploadMsg = 'URL 导入成功';
      this.urlText = '';
    },

    async generateOutline() {
      if (!this.currentProject) return;
      this.genLoading = true;
      try {
        const r = await this.api('POST', `/projects/${this.currentProject.id}/outline`);
        this.slides = r.slides || [];
        this.page = 'outline';
      } catch (e) { this.error = e.message; }
      finally { this.genLoading = false; }
    },

    goToInput() { this.page = 'input'; },

    // ─── Outline ───
    addSlide() {
      this.slides.push({ id: this.slides.length + 1, title: '新页面', content: '', layout: 'content-text', notes: '' });
      this.renumber();
    },
    delSlide(i) { this.slides.splice(i, 1); this.renumber(); },
    moveSlide(i, dir) {
      const j = i + dir;
      if (j < 0 || j >= this.slides.length) return;
      [this.slides[i], this.slides[j]] = [this.slides[j], this.slides[i]];
      this.renumber();
    },
    renumber() { this.slides.forEach((s, i) => s.id = i + 1); },

    async confirmOutline() {
      if (!this.currentProject) return;
      await this.api('PUT', `/projects/${this.currentProject.id}/outline`, { slides: this.slides, confirmed: true });
      await this.loadStyles();
      this.page = 'style';
    },

    goToOutline() { this.page = 'outline'; },

    // ─── Style ───
    async loadStyles() {
      try { this.styles = await this.api('GET', '/styles'); } catch (e) { console.error(e); }
    },
    selectStyle(id) {
      this.styleId = id;
      const s = this.styles.find(x => x.id === id);
      if (s) this.styleName = s.name_cn;
    },
    async confirmStyle() {
      if (!this.currentProject || !this.styleId) return;
      const r = await this.api('POST', `/projects/${this.currentProject.id}/style`, { style_id: this.styleId, mode_id: 'narrative' });
      this.designColors = r.colors || {};
      this.designFonts = r.fonts || {};
      this.page = 'confirm';
    },
    goToStyle() { this.page = 'style'; },

    // ─── Generate ───
    async submitGen() {
      if (!this.currentProject) return;
      try {
        const r = await this.api('POST', `/projects/${this.currentProject.id}/generate`);
        this.taskId = r.task_id;
        this.progressPct = 0;
        this.progressText = '提交成功，开始生成...';
        this.taskSteps = [
          { name: '设计规范生成', status: 'pending' },
          { name: 'SVG 逐页生成', status: 'pending' },
          { name: '演讲者备注', status: 'pending' },
          { name: '后处理导出', status: 'pending' },
        ];
        this.taskDone = false;
        this.taskError = '';
        this.downloadUrl = '';
        this.page = 'progress';
        this.startPolling();
      } catch (e) { this.error = e.message; }
    },

    // ─── Polling ───
    startPolling() {
      this.stopPolling();
      this.pollTimer = setInterval(() => this.pollTask(), 3000);
      this.pollTask();
    },
    stopPolling() { if (this.pollTimer) { clearInterval(this.pollTimer); this.pollTimer = null; } },

    async pollTask() {
      if (!this.taskId) return;
      try {
        const t = await this.api('GET', `/tasks/${this.taskId}`);
        this.progressPct = Math.round((t.progress || 0) * 100);
        this.progressText = `${this.progressPct}% - ${t.current_step || '处理中...'}`;
        this.taskSteps = (t.steps || []).map(s => ({
          name: { Design: '设计规范生成', SVG: 'SVG 逐页生成', Notes: '演讲者备注', Export: '后处理导出' }[s.name] || s.name,
          status: s.status,
          detail: s.detail || ''
        }));
        if (t.status === 'completed') {
          this.stopPolling();
          this.taskDone = true;
          this.progressText = '100% - 生成完成！';
          if (t.result?.export_path) this.downloadUrl = '/api/' + t.result.export_path;
        } else if (t.status === 'failed') {
          this.stopPolling();
          this.taskError = t.error || '生成失败';
        }
      } catch (e) { /* retry */ }
    },
  }
}).mount('#app');