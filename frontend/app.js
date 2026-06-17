const { createApp } = Vue;

const App = {
  data() {
    return {
      page: 'home', step: 0,
      steps: ['内容输入', 'AI大纲', '视觉风格', '确认生成', '生成进度'],
      toast: { show: false, msg: '', type: 'success' },
      toastTimer: null,
      loading: false, homeError: '', projects: [],
      newName: '', creating: false,
      currentProject: null,
      topicText: '', hasTopic: false,
      urlText: '', uploading: false, uploadMsg: '', uploadOk: false,
      generating: false, dragOver: false,
      slides: [], slideKey: 0,
      layouts: ['cover','content-text','content-image','comparison','chart','timeline','list','ending'],
      styles: [], styleLoading: false, styleId: '', styleName: '',
      modeId: 'narrative', modes: ['narrative','briefing','instructional','pyramid','showcase'],
      designColors: {}, designFonts: {},
      submitting: false,
      taskId: '', progressPct: 0, progressText: '准备中...', progressLabel: '',
      taskSteps: [], taskDone: false, taskError: '', downloadUrl: '',
      pollTimer: null,
    };
  },
  computed: {
    modeName() {
      return { narrative:'叙事型', briefing:'简报型', instructional:'教学型',
               pyramid:'金字塔型', showcase:'展示型' }[this.modeId] || this.modeId;
    }
  },
  watch: {
    page(val) {
      const map = { home:0, input:1, outline:2, style:3, confirm:4, progress:5 };
      this.step = map[val] || 0;
    }
  },
  mounted() {
    this.loadProjects();
    this.loadStyles();
  },
  methods: {
    fmtDate(d) {
      if (!d) return '';
      return new Date(d).toLocaleString('zh-CN', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
    },
    showToast(msg, type, duration) {
      type = type || 'success'; duration = duration || 3000;
      if (this.toastTimer) clearTimeout(this.toastTimer);
      this.toast = { show: true, msg, type };
      this.toastTimer = setTimeout(() => { this.toast.show = false; }, duration);
    },
    async api(method, path, body) {
      const opts = { method, headers: {} };
      if (body instanceof FormData) opts.body = body;
      else if (body != null) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
      let r;
      try {
        r = await fetch('/api' + path, opts);
      } catch (e) {
        throw new Error('网络错误：无法连接到服务器');
      }
      if (!r.ok) {
        let msg;
        try { const j = await r.json(); msg = j.detail || JSON.stringify(j).slice(0,200); }
        catch (e) { msg = r.statusText; }
        throw new Error(msg);
      }
      const text = await r.text();
      return text ? JSON.parse(text) : null;
    },
    goHome() { this.stopPolling(); this.page = 'home'; this.loadProjects(); },
    goToInput() { this.page = 'input'; },
    goToOutline() { this.page = 'outline'; },
    goToStep(i) {
      const pages = ['', 'input', 'outline', 'style', 'confirm', 'progress'];
      if (i > 0 && i < pages.length) this.page = pages[i];
    },
    async loadProjects() {
      this.loading = true;
      try { this.projects = await this.api('GET', '/projects') || []; }
      catch (e) { this.homeError = e.message; }
      finally { this.loading = false; }
    },
    async createProject() {
      if (!this.newName.trim()) return;
      this.creating = true;
      try {
        const p = await this.api('POST', '/projects', { name: this.newName.trim(), format: 'ppt169' });
        this.currentProject = p;
        this.newName = '';
        this.showToast('项目创建成功');
        this.page = 'input';
        await this.loadProjects();
      } catch (e) { this.showToast(e.message, 'error'); }
      finally { this.creating = false; }
    },
    async openProject(p) {
      try {
        const proj = await this.api('GET', '/projects/' + encodeURIComponent(p.id));
        this.currentProject = proj;
        this.topicText = proj.topic || '';
        this.hasTopic = !!proj.topic;
        this.slides = (proj.outline && proj.outline.slides) || [];
        this.styleId = (proj.design && proj.design.style_id) || '';
        this.styleName = this.getStyleName(this.styleId);
        this.modeId = (proj.design && proj.design.mode_id) || 'narrative';
        this.designColors = (proj.design && proj.design.colors) || {};
        this.designFonts = (proj.design && proj.design.fonts) || {};
        switch (proj.status) {
          case 'created': case 'sourcing': this.page = 'input'; break;
          case 'outlining': this.page = 'outline'; break;
          case 'styling': case 'ready': this.page = 'confirm'; break;
          case 'generating': this.page = 'progress'; this.startPolling(); break;
          default: this.page = 'input';
        }
      } catch (e) { this.showToast(e.message, 'error'); }
    },
    async deleteProject(p) {
      if (!confirm('确定删除项目「' + p.name + '」？所有数据将被清除。')) return;
      try {
        await this.api('DELETE', '/projects/' + encodeURIComponent(p.id));
        this.showToast('已删除');
        this.loadProjects();
      } catch (e) { this.showToast(e.message, 'error'); }
    },
    getStyleName(id) { const s = this.styles.find(x => x.id === id); return s ? s.name_cn : id; },
    async saveTopic() {
      if (!this.currentProject || !this.topicText.trim()) return;
      try {
        await this.api('PUT', '/projects/' + this.currentProject.id + '/topic', { topic: this.topicText });
        this.hasTopic = true;
        this.showToast('主题已保存');
      } catch (e) { this.showToast(e.message, 'error'); }
    },
    async uploadFiles(e) {
      const files = e.target ? e.target.files : e;
      if (!files || !files.length) return;
      this.uploading = true;
      const fd = new FormData();
      for (const f of files) fd.append('files', f);
      try {
        const r = await this.api('POST', '/projects/' + this.currentProject.id + '/sources', fd);
        this.uploadMsg = '上传 ' + r.sources.length + ' 个文件成功';
        this.uploadOk = true;
      } catch (e) { this.uploadMsg = '上传失败：' + e.message; this.uploadOk = false; }
      finally { this.uploading = false; setTimeout(() => this.uploadMsg = '', 4000); }
    },
    onDrop(e) { this.dragOver = false; this.uploadFiles(e.dataTransfer.files); },
    async importUrl() {
      if (!this.urlText.trim() || !this.currentProject) return;
      try {
        await this.api('POST', '/projects/' + this.currentProject.id + '/sources/url', { url: this.urlText.trim() });
        this.showToast('链接导入成功');
        this.urlText = '';
      } catch (e) { this.showToast(e.message, 'error'); }
    },
    async generateOutline() {
      if (!this.currentProject) { this.showToast('请先创建项目', 'error'); return; }
      this.generating = true;
      try {
        const r = await this.api('POST', '/projects/' + this.currentProject.id + '/outline');
        this.slides = (r && r.slides) || [];
        this.showToast('大纲生成完成：' + this.slides.length + ' 页');
        this.page = 'outline';
      } catch (e) { this.showToast(e.message, 'error'); }
      finally { this.generating = false; }
    },
    addSlide() {
      this.slideKey++;
      this.slides.push({ id: this.slides.length + 1, title: '', content: '', layout: 'content-text', notes: '', _key: this.slideKey });
      this.renumber();
    },
    delSlide(i) {
      if (this.slides.length <= 2) return;
      this.slides.splice(i, 1); this.renumber();
    },
    moveSlide(i, dir) {
      const j = i + dir;
      if (j < 0 || j >= this.slides.length) return;
      var tmp = this.slides[i]; this.slides[i] = this.slides[j]; this.slides[j] = tmp;
      this.renumber();
    },
    renumber() { this.slides.forEach(function(s, i) { s.id = i + 1; }); },
    async confirmOutline() {
      if (!this.currentProject) return;
      try {
        await this.api('PUT', '/projects/' + this.currentProject.id + '/outline', { slides: this.slides, confirmed: true });
        this.showToast('大纲已确认');
        this.page = 'style';
      } catch (e) { this.showToast(e.message, 'error'); }
    },
    async loadStyles() {
      this.styleLoading = true;
      try { this.styles = await this.api('GET', '/styles') || []; }
      catch (e) { console.error(e); }
      finally { this.styleLoading = false; }
    },
    selectStyle(id) {
      this.styleId = id;
      const s = this.styles.find(function(x) { return x.id === id; });
      if (s) this.styleName = s.name_cn;
    },
    styleColor(id) {
      var map = { 'swiss-minimal':'#3b82f6', 'soft-rounded':'#10b981', 'glassmorphism':'#8b5cf6',
        'dark-tech':'#1e293b', 'blueprint':'#0891b2', 'editorial':'#dc2626',
        'photo-editorial':'#d946ef', 'data-journalism':'#059669', 'brutalist':'#92400e',
        'memphis':'#f97316', 'zine':'#ec4899', 'vintage-poster':'#b45309',
        'paper-cut':'#65a30d', 'sketch-notes':'#ca8a04', 'ink-notes':'#1e293b',
        'chalkboard':'#374151', 'ink-wash':'#78716c' };
      return map[id] || '#5b8def';
    },
    async confirmStyle() {
      if (!this.currentProject || !this.styleId) return;
      try {
        var r = await this.api('POST', '/projects/' + this.currentProject.id + '/style', { style_id: this.styleId, mode_id: this.modeId });
        this.designColors = (r && r.colors) || {};
        this.designFonts = (r && r.fonts) || {};
        this.showToast('风格已选择');
        this.page = 'confirm';
      } catch (e) { this.showToast(e.message, 'error'); }
    },
    async submitGen() {
      if (!this.currentProject) return;
      this.submitting = true;
      try {
        var r = await this.api('POST', '/projects/' + this.currentProject.id + '/generate');
        this.taskId = r.task_id;
        this.progressPct = 0; this.progressText = '任务已提交'; this.progressLabel = '准备中';
        this.taskSteps = [
          { name: '设计规范生成', status: 'pending', detail: '' },
          { name: 'SVG 逐页生成', status: 'pending', detail: '' },
          { name: '演讲者备注', status: 'pending', detail: '' },
          { name: '后处理导出', status: 'pending', detail: '' },
        ];
        this.taskDone = false; this.taskError = ''; this.downloadUrl = '';
        this.page = 'progress';
        this.startPolling();
      } catch (e) { this.showToast(e.message, 'error'); }
      finally { this.submitting = false; }
    },
    startPolling() {
      this.stopPolling();
      this.pollTimer = setInterval(this.pollTask, 3000);
      this.pollTask();
    },
    stopPolling() {
      if (this.pollTimer) { clearInterval(this.pollTimer); this.pollTimer = null; }
    },
    async pollTask() {
      if (!this.taskId) return;
      try {
        var t = await this.api('GET', '/tasks/' + this.taskId);
        var pct = Math.round((t.progress || 0) * 100);
        this.progressPct = Math.min(pct, 99);
        this.progressText = t.current_step || '处理中...';
        this.progressLabel = pct + '%';
        var nameMap = { 'Design':'设计规范生成','SVG':'SVG逐页生成','Notes':'演讲者备注','Export':'后处理导出',
          'Strategist Design Spec':'设计规范生成','Executor SVG Gen':'SVG逐页生成','Speaker Notes':'演讲者备注','Post-processing':'后处理导出' };
        this.taskSteps = (t.steps || []).map(function(s) {
          return { name: nameMap[s.name] || s.name, status: s.status, detail: s.detail || '' };
        });
        if (t.status === 'completed') {
          this.stopPolling();
          this.taskDone = true;
          this.progressPct = 100;
          this.progressText = '生成完成！';
          if (t.result && t.result.export_path) this.downloadUrl = '/api/' + t.result.export_path;
        } else if (t.status === 'failed') {
          this.stopPolling();
          this.taskError = t.error || '生成失败，请重试';
        }
      } catch (e) { /* silent retry */ }
    },
  }
};

const app = createApp(App);

app.component('StatusBadge', {
  props: ['status'],
  template: '<span :class="[\'status-badge\', status]">{{ label }}</span>',
  computed: {
    label() {
      var map = { created:'已创建', sourcing:'内容输入', outlining:'大纲编辑', styling:'选风格',
                  ready:'待生成', generating:'生成中', done:'已完成', failed:'失败' };
      return map[this.status] || this.status;
    }
  }
});

app.mount('#app');