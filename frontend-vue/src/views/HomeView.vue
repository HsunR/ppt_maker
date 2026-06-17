<template>
  <div>
    <div class="home-hero">
      <h1>AI PPT 生成服务</h1>
      <p>上传文档或输入主题，AI 自动生成原生可编辑的 PowerPoint 文件</p>
    </div>
    <div class="create-card">
      <input v-model="newName" placeholder="项目名称，如「AI行业趋势2026」" @keyup.enter="createProject" :disabled="creating">
      <button class="btn btn-primary" @click="createProject" :disabled="creating||!newName.trim()">{{ creating?'创建中...':'+ 创建项目' }}</button>
    </div>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="projects.length===0" class="empty-state"><p>暂无项目，创建一个开始吧</p></div>
    <div v-else>
      <div v-for="p in projects" :key="p.id" class="project-card" @click="openProject(p)">
        <div class="pc-left"><div class="pc-name">{{ p.name }}</div><div class="pc-meta">{{ fmtDate(p.updated_at||p.created_at) }}</div></div>
        <StatusBadge :status="p.status" />
        <button class="btn-icon danger" @click.stop="deleteProject(p)">&times;</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { store, api, fmtDate, showToast } from '../api'

export default {
  setup() {
    const router = useRouter()
    const loading = ref(true)
    const creating = ref(false)
    const newName = ref('')
    const projects = ref([])

    async function loadProjects() {
      loading.value = true
      try { projects.value = await api('GET', '/projects') || [] } catch (e) { showToast(e.message, 'error') }
      finally { loading.value = false }
    }
    async function createProject() {
      if (!newName.value.trim()) return
      creating.value = true
      try {
        const p = await api('POST', '/projects', { name: newName.value.trim(), format: 'ppt169' })
        store.currentProject = p
        newName.value = ''
        showToast('项目创建成功')
        router.push('/input')
        await loadProjects()
      } catch (e) { showToast(e.message, 'error') }
      finally { creating.value = false }
    }
    async function openProject(p) {
      try {
        const proj = await api('GET', '/projects/' + encodeURIComponent(p.id))
        store.currentProject = proj
        const st = proj.status
        if (['created','sourcing'].includes(st)) router.push('/input')
        else if (st === 'outlining') { store.slides = proj.outline?.slides || []; router.push('/outline') }
        else if (['styling','ready'].includes(st)) {
          store.slides = proj.outline?.slides || []
          store.designColors = proj.design?.colors || {}
          store.designFonts = proj.design?.fonts || {}
          router.push('/confirm')
        }
        else router.push('/input')
      } catch (e) { showToast(e.message, 'error') }
    }
    async function deleteProject(p) {
      if (!confirm('确定删除「' + p.name + '」？')) return
      try { await api('DELETE', '/projects/' + encodeURIComponent(p.id)); showToast('已删除'); loadProjects() }
      catch (e) { showToast(e.message, 'error') }
    }
    onMounted(loadProjects)
    return { loading, creating, newName, projects, createProject, openProject, deleteProject, fmtDate }
  }
}
</script>