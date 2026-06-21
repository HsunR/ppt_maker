<template>
  <div>
    <h2>1. 内容输入</h2>
    <p class="page-desc">输入主题描述、上传源文件或粘贴网页链接，AI 将分析内容生成 PPT 大纲。</p>

    <div class="card">
      <textarea v-model="topicText" rows="5" placeholder="例如：2026年人工智能行业趋势分析报告..." style="width:100%"></textarea>
      <div class="actions" style="margin-top:8px">
        <button class="btn btn-primary btn-sm" @click="saveTopic" :disabled="!topicText.trim()">保存主题</button>
        <span v-if="hasTopic" style="color:var(--success);font-size:13px">&#10003; 已保存</span>
      </div>
    </div>

    <div class="card">
      <div class="drop-zone" @click="$refs.fi.click()" @dragover.prevent @drop.prevent="onDrop">
        <div class="dz-text">{{ upText }}</div>
        <input type="file" ref="fi" multiple style="display:none" @change="onFileChange">
      </div>
      <div v-if="upMsg" style="color:var(--success);font-size:13px;margin-top:6px">{{ upMsg }}</div>
    </div>

    <div class="card">
      <div class="row"><input v-model="urlText" placeholder="https://..." @keyup.enter="importUrl" style="flex:1"><button class="btn" @click="importUrl" :disabled="!urlText.trim()">导入</button></div>
    </div>

    <div class="actions">
      <button class="btn btn-primary btn-lg" @click="generateOutline" :disabled="genLoading">{{ genLoading ? '生成中...' : 'AI 生成大纲 &#9654;' }}</button>
    </div>
    <div v-if="errMsg" class="error-box">{{ errMsg }}</div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { store, api, showToast } from '../api'

export default {
  setup() {
    const router = useRouter()
    const topicText = ref(store.topicText || '')
    const hasTopic = ref(store.hasTopic)
    const urlText = ref('')
    const upText = ref('&#128194; 点击选择文件或拖拽到此处')
    const upMsg = ref('')
    const genLoading = ref(false)
    const errMsg = ref('')
    const upFiles = ref([])

    async function saveTopic() {
      if (!store.currentProject?.id) { showToast('请先打开项目', 'error'); return }
      try {
        await api('PUT', '/projects/' + store.currentProject.id + '/topic', { topic: topicText.value })
        store.topicText = topicText.value
        hasTopic.value = true
        showToast('主题已保存')
      } catch (e) { showToast(e.message, 'error') }
    }
    async function onFileChange(e) {
      if (!store.currentProject?.id) { showToast('请先打开项目', 'error'); return }
      const files = e.target.files; if (!files.length) return
      const fd = new FormData()
      for (const f of files) fd.append('files', f)
      upText.value = '上传中...'
      try {
        const r = await api('POST', '/projects/' + store.currentProject.id + '/sources', fd)
        upMsg.value = '上传 ' + r.sources.length + ' 个文件成功'
        setTimeout(() => upMsg.value = '', 4000)
      } catch (e) { showToast(e.message, 'error') }
      finally { upText.value = '&#128194; 点击选择文件或拖拽到此处' }
    }
    function onDrop(e) { upFiles.value = e.dataTransfer.files; onFileChange({ target: { files: e.dataTransfer.files } }) }
    async function importUrl() {
      if (!store.currentProject?.id) { showToast('请先打开项目', 'error'); return }
      try {
        await api('POST', '/projects/' + store.currentProject.id + '/sources/url', { url: urlText.value.trim() })
        showToast('导入成功'); urlText.value = ''
      } catch (e) { showToast(e.message, 'error') }
    }
    async function generateOutline() {
      if (!store.currentProject?.id) { errMsg.value = '请先打开项目'; return }
      genLoading.value = true; errMsg.value = ''
      try {
        const r = await api('POST', '/projects/' + store.currentProject.id + '/outline')
        store.slides = r?.slides || []
        showToast('大纲生成完成：' + store.slides.length + ' 页')
        router.push('/outline')
      } catch (e) { errMsg.value = e.message }
      finally { genLoading.value = false }
    }
    return { topicText, hasTopic, urlText, upText, upMsg, genLoading, errMsg, saveTopic, onFileChange, onDrop, importUrl, generateOutline }
  }
}
</script>