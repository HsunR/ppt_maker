<template>
  <div>
    <h2>2. AI 大纲 <span class="count-badge">{{ slides.length }} 页</span></h2>
    <p class="page-desc">编辑大纲，可修改标题、内容和布局，支持增删排序。</p>
    <div v-if="slides.length===0" class="empty-state"><p>尚未生成大纲</p></div>
    <div v-for="(s, i) in slides" :key="i" class="slide-block">
      <div class="slide-header">
        <span class="slide-idx">#{{ s.id }}</span>
        <span class="slide-layout-tag">{{ s.layout }}</span>
        <div style="margin-left:auto;display:flex;gap:4px">
          <button class="btn-icon" @click="move(i,-1)" :disabled="i===0">&#8593;</button>
          <button class="btn-icon" @click="move(i,1)" :disabled="i===slides.length-1">&#8595;</button>
          <button class="btn-icon danger" @click="del(i)">&#10005;</button>
        </div>
      </div>
      <div class="slide-body">
        <input v-model="s.title" placeholder="页面标题" style="width:100%;font-weight:600;margin-bottom:4px">
        <textarea v-model="s.content" placeholder="内容要点" rows="2" style="width:100%;margin-bottom:4px"></textarea>
        <select v-model="s.layout" style="margin-right:8px">
          <option v-for="l in layouts" :key="l" :value="l">{{ l }}</option>
        </select>
        <input v-model="s.notes" placeholder="备注（可选）" style="width:300px">
      </div>
    </div>
    <div class="actions">
      <button class="btn" @click="add">+ 添加页面</button>
      <span style="flex:1"></span>
      <button class="btn btn-primary btn-lg" @click="confirm" :disabled="slides.length<2">确认大纲 &#9654;</button>
    </div>
    <div v-if="errMsg" class="error-box">{{ errMsg }}</div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { store, api, showToast } from '../api'

export default {
  setup() {
    const router = useRouter()
    const layouts = ['cover','content-text','content-image','comparison','chart','timeline','list','ending']
    const slides = computed({ get: () => store.slides, set: v => store.slides = v })
    const errMsg = ref('')

    function renumber() { store.slides.forEach((s,i) => s.id = i+1) }
    function add() { store.slides.push({ id: store.slides.length+1, title:'', content:'', layout:'content-text', notes:'' }); renumber() }
    function del(i) { if (store.slides.length > 2) { store.slides.splice(i,1); renumber() } }
    function move(i,d) { const j=i+d; if(j<0||j>=store.slides.length) return; [store.slides[i],store.slides[j]]=[store.slides[j],store.slides[i]]; renumber() }
    async function confirm() {
      if (!store.currentProject?.id) { errMsg.value = '请先打开项目'; return }
      try {
        await api('PUT', '/projects/'+store.currentProject.id+'/outline', { slides: store.slides, confirmed: true })
        showToast('大纲已确认')
        router.push('/style')
      } catch (e) { errMsg.value = e.message }
    }
    return { slides, layouts, errMsg, add, del, move, confirm }
  }
}
</script>