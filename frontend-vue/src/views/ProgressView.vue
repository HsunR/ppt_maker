<template>
  <div>
    <h2>5. 生成进度</h2>
    <p class="page-desc">PPT 正在生成中。刷新页面不会中断。完成后可下载。</p>

    <!-- Progress -->
    <div class="card progress-card">
      <div class="pg-pct">{{ progressPct }}%</div>
      <div class="pg-status-text">{{ progressText }}</div>
      <div class="progress-track"><div class="progress-fill" :style="{width:progressPct+'%'}"></div></div>
    </div>

    <div class="steps-v">
      <div v-for="s in taskSteps" :key="s.name" :class="['sv', s.status]">
        <div class="sv-icon" v-html="{completed:'&#10003;', running:'&#9654;', failed:'&#10007;', pending:'&#9679;'}[s.status]"></div>
        <div><div class="sv-name">{{ s.name }}</div><div v-if="s.detail" style="font-size:12px;color:var(--t2)">{{ s.detail }}</div></div>
      </div>
    </div>

    <!-- ═══════ SVG Preview Gallery ═══════ -->
    <div v-if="svgFiles.length || taskRunning" class="card">
      <div class="card-header">
        <h3>已生成的页面 ({{ svgFiles.length }})</h3>
        <span v-if="svgLoading" class="loading" style="padding:0;font-size:12px">刷新中...</span>
      </div>
      <div v-if="svgFiles.length === 0" style="color:var(--t3);font-size:14px;text-align:center;padding:12px">
        等待第一页生成...
      </div>
      <div class="svg-grid">
        <div v-for="svg in svgFiles" :key="svg.name" class="svg-thumb">
          <div class="svg-preview">
            <img :src="svgUrl(svg.name)" :alt="svg.name" @error="onImgError($event)">
          </div>
          <div class="svg-label">{{ svg.name }}</div>
        </div>
      </div>
    </div>

    <!-- ═══════ Step Review (read-only) ═══════ -->
    <div class="card">
      <div class="card-header"><h3>项目信息回顾（只读）</h3></div>
      <div class="review-section" @click="showTopic = !showTopic">
        <div class="review-header"><span class="review-icon">{{ showTopic ? '&#9660;' : '&#9654;' }}</span>1. 内容输入</div>
        <div v-if="showTopic" class="review-body">
          <div v-if="topicText" style="white-space:pre-wrap;font-size:14px;color:var(--t2)">{{ topicText }}</div>
          <div v-else style="color:var(--t3)">未设置主题</div>
        </div>
      </div>
      <div class="review-section" @click="showOutline = !showOutline">
        <div class="review-header"><span class="review-icon">{{ showOutline ? '&#9660;' : '&#9654;' }}</span>2. AI 大纲（{{ slides.length }} 页）</div>
        <div v-if="showOutline" class="review-body">
          <div v-for="s in slides" :key="s.id" class="review-slide">
            <span class="rs-idx">{{ s.id }}.</span>
            <span class="rs-title">{{ s.title || '(无标题)' }}</span>
            <span class="rs-layout">{{ s.layout }}</span>
          </div>
        </div>
      </div>
      <div class="review-section" @click="showStyle = !showStyle">
        <div class="review-header"><span class="review-icon">{{ showStyle ? '&#9660;' : '&#9654;' }}</span>3. 视觉风格</div>
        <div v-if="showStyle" class="review-body">
          <div style="font-size:14px;color:var(--t2)">风格：{{ styleName || styleId || '未选择' }}</div>
          <div v-if="styleId" style="font-size:14px;color:var(--t2)">主色：<span class="color-chip" :style="{background:designColors.primary}"></span>{{ designColors.primary }} 字体：{{ designFonts.heading }}</div>
        </div>
      </div>
    </div>

    <!-- Result -->
    <div v-if="taskDone" style="text-align:center;padding:32px;background:var(--surface);border:1px solid var(--success);border-radius:var(--radius);margin-top:16px">
      <div style="font-size:48px;margin-bottom:12px">&#9989;</div>
      <div style="font-size:20px;font-weight:600;color:var(--success);margin-bottom:20px">PPT 生成完成！</div>
      <div class="actions" style="justify-content:center">
        <a :href="downloadUrl" class="btn btn-primary btn-lg" download>&#128229; 下载 PPTX</a>
        <button class="btn" @click="$router.push('/')">返回首页</button>
      </div>
    </div>
    <div v-if="taskError" class="error-box">{{ taskError }}</div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { store, api, showToast } from '../api'

export default {
  setup() {
    const route = useRoute()
    // Polling state
    const progressPct = ref(store.progressPct || 0)
    const progressText = ref(store.progressText || '准备中...')
    const taskSteps = ref(store.taskSteps.length ? store.taskSteps : [
      {name:'设计规范生成',status:'pending',detail:''},{name:'SVG逐页生成',status:'pending',detail:''},
      {name:'演讲者备注',status:'pending',detail:''},{name:'后处理导出',status:'pending',detail:''}])
    const taskDone = ref(store.taskDone || false)
    const taskError = ref(store.taskError || '')
    const downloadUrl = ref(store.downloadUrl || '')
    const taskRunning = ref(false)

    // SVG preview
    const svgFiles = ref([])
    const svgLoading = ref(false)
    const projectId = ref(store.currentProject?.id || '')

    // Review sections
    const showTopic = ref(false)
    const showOutline = ref(false)
    const showStyle = ref(false)
    const topicText = ref(store.topicText || '')
    const slides = computed(() => store.slides)
    const styleId = computed(() => store.styleId)
    const styleName = ref(store.styleName || '')
    const designColors = computed(() => store.designColors)
    const designFonts = computed(() => store.designFonts)

    let pollTimer = null
    let svgTimer = null

    const nameMap = { 'Design':'设计规范生成','SVG':'SVG逐页生成','Notes':'演讲者备注','Export':'后处理导出',
      'Strategist Design Spec':'设计规范生成','Executor SVG Gen':'SVG逐页生成','Speaker Notes':'演讲者备注','Post-processing':'后处理导出' }

    function svgUrl(name) { return projectId.value ? '/api/projects/' + encodeURIComponent(projectId.value) + '/svg/' + name : '' }

    function onImgError(e) {
      // Hide broken SVGs gracefully
      e.target.style.display = 'none'
    }

    async function pollSvg() {
      if (!projectId.value) return
      svgLoading.value = true
      try {
        const r = await api('GET', '/projects/' + encodeURIComponent(projectId.value) + '/svg')
        svgFiles.value = r?.svg_files || []
      } catch (e) { /* project might not exist yet */ }
      finally { svgLoading.value = false }
    }

    async function pollTask() {
      if (!store.taskId) return
      try {
        const t = await api('GET', '/tasks/' + store.taskId)
        const pct = Math.round((t.progress||0)*100)
        progressPct.value = Math.min(pct, 99)
        progressText.value = t.current_step || '处理中...'
        taskRunning.value = t.status === 'running' || t.status === 'pending'
        store.progressPct = progressPct.value; store.progressText = progressText.value
        taskSteps.value = (t.steps||[]).map(s => ({ name: nameMap[s.name]||s.name, status: s.status, detail: s.detail||'' }))
        store.taskSteps = taskSteps.value

        if (t.status === 'completed') {
          clearInterval(pollTimer); clearInterval(svgTimer)
          taskDone.value = true; store.taskDone = true
          progressPct.value = 100; progressText.value = '生成完成！'
          if (t.result?.export_path) { downloadUrl.value = '/'+t.result.export_path; store.downloadUrl = downloadUrl.value }
        } else if (t.status === 'failed') {
          clearInterval(pollTimer); clearInterval(svgTimer)
          taskError.value = t.error || '生成失败'; store.taskError = taskError.value
        }
      } catch (e) { /* retry */ }
    }

    onMounted(() => {
      if (store.taskId) {
        pollTask(); pollTimer = setInterval(pollTask, 3000)
        pollSvg(); svgTimer = setInterval(pollSvg, 5000)
      }
    })
    onUnmounted(() => {
      if (pollTimer) clearInterval(pollTimer)
      if (svgTimer) clearInterval(svgTimer)
    })

    return { progressPct, progressText, taskSteps, taskDone, taskError, downloadUrl, taskRunning,
      svgFiles, svgLoading, svgUrl, onImgError, projectId,
      showTopic, showOutline, showStyle, topicText, slides, styleId, styleName, designColors, designFonts }
  }
}
</script>

<style scoped>
.svg-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 10px; margin-top: 8px; }
.svg-thumb { background: var(--s2); border: 1px solid var(--border); border-radius: var(--rs); overflow: hidden; }
.svg-preview { height: 90px; display: flex; align-items: center; justify-content: center; padding: 4px; }
.svg-preview img { max-width: 100%; max-height: 100%; }
.svg-label { font-size: 11px; color: var(--t2); text-align: center; padding: 4px; background: var(--s3); }

.review-section { border-bottom: 1px solid var(--border); cursor: pointer; }
.review-section:last-child { border-bottom: none; }
.review-header { padding: 10px 4px; font-size: 15px; font-weight: 500; display: flex; align-items: center; gap: 8px; }
.review-icon { font-size: 10px; color: var(--t3); }
.review-body { padding: 4px 4px 12px 20px; }
.review-slide { display: flex; gap: 8px; padding: 4px 0; font-size: 13px; }
.rs-idx { color: var(--primary); font-weight: 600; min-width: 20px; }
.rs-title { flex: 1; }
.rs-layout { font-size: 11px; color: var(--t3); padding: 1px 6px; background: var(--s3); border-radius: 99px; }
.color-chip { display: inline-block; width: 14px; height: 14px; border-radius: 3px; vertical-align: middle; margin-right: 4px; }
</style>