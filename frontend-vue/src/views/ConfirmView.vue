<template>
  <div>
    <h2>4. 确认并生成</h2>
    <p class="page-desc">确认设计概览，然后提交 PPT 生成任务。</p>
    <div class="card">
      <div class="card-header"><h3>设计概览</h3></div>
      <div class="preview-grid">
        <div class="pg-item"><span>页数</span><strong>{{ slides.length }}</strong></div>
        <div class="pg-item"><span>风格</span>{{ styleId }}</div>
        <div class="pg-item"><span>模式</span>{{ modeLabels[modeId]||modeId }}</div>
        <div class="pg-item"><span>主色</span>{{ designColors.primary }}</div>
        <div class="pg-item"><span>辅色</span>{{ designColors.secondary }}</div>
        <div class="pg-item"><span>字体</span>{{ designFonts.heading }}</div>
      </div>
    </div>
    <div class="card">
      <div class="card-header"><h3>大纲预览（{{ slides.length }} 页）</h3></div>
      <div v-for="s in slides" :key="s.id" style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid var(--border);font-size:14px">
        <span style="color:var(--primary);font-weight:600;min-width:24px">{{ s.id }}.</span>
        <span style="flex:1">{{ s.title || '(无标题)' }}</span>
        <span style="font-size:11px;color:var(--t3);padding:2px 8px;background:var(--s3);border-radius:99px">{{ s.layout }}</span>
      </div>
    </div>
    <div class="actions" style="justify-content:space-between">
      <button class="btn" @click="$router.push('/style')">&larr; 修改风格</button>
      <button class="btn btn-accent btn-lg" @click="submitGen" :disabled="submitting">{{ submitting?'提交中...':'&#9889; 开始生成 PPT' }}</button>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { store, api, showToast } from '../api'

export default {
  setup() {
    const router = useRouter()
    const submitting = ref(false)
    const slides = computed(() => store.slides)
    const styleId = computed(() => store.styleId)
    const modeId = computed(() => store.modeId)
    const designColors = computed(() => store.designColors)
    const designFonts = computed(() => store.designFonts)
    const modeLabels = { narrative:'叙事型', briefing:'简报型', instructional:'教学型', pyramid:'金字塔型', showcase:'展示型' }

    async function submitGen() {
      if (!store.currentProject?.id) { showToast('请先打开项目', 'error'); return }
      submitting.value = true
      try {
        const r = await api('POST', '/projects/'+store.currentProject.id+'/generate')
        store.taskId = r.task_id; store.progressPct = 0; store.progressText = '任务已提交'
        store.taskSteps = [{name:'设计规范生成',status:'pending',detail:''},{name:'SVG逐页生成',status:'pending',detail:''},{name:'演讲者备注',status:'pending',detail:''},{name:'后处理导出',status:'pending',detail:''}]
        store.taskDone = false; store.taskError = ''; store.downloadUrl = ''
        router.push('/progress')
      } catch (e) { showToast(e.message, 'error') }
      finally { submitting.value = false }
    }
    return { slides, styleId, modeId, designColors, designFonts, modeLabels, submitting, submitGen }
  }
}
</script>