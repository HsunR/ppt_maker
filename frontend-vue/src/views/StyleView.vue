<template>
  <div>
    <h2>3. 视觉风格</h2>
    <p class="page-desc">选择 PPT 的视觉风格，决定配色、字体和整体装饰语言。</p>
    <div v-if="loading" class="loading">加载风格中...</div>
    <div v-else class="style-grid">
      <div v-for="st in styles" :key="st.id" :class="['style-card',{selected:styleId===st.id}]" @click="select(st.id)">
        <div class="sc-name">{{ st.name_cn }}</div>
        <div class="sc-en">{{ st.name }}</div>
        <div class="sc-desc">{{ st.character }}</div>
      </div>
    </div>
    <div class="card" v-if="styleId">
      <div class="card-header"><h3>已选：{{ styleName }}</h3></div>
      <div class="row"><label>叙事模式：</label>
        <select v-model="modeId">
          <option v-for="m in modes" :key="m" :value="m">{{ modeLabels[m]||m }}</option>
        </select>
      </div>
    </div>
    <div class="actions">
      <button class="btn" @click="$router.push('/outline')">&larr; 修改大纲</button>
      <button class="btn btn-primary btn-lg" @click="confirmStyle" :disabled="!styleId">确认风格 &#9654;</button>
    </div>
    <div v-if="errMsg" class="error-box">{{ errMsg }}</div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { store, api, showToast } from '../api'

export default {
  setup() {
    const router = useRouter()
    const loading = ref(true)
    const styles = ref([])
    const styleId = ref(store.styleId || '')
    const styleName = ref(store.styleName || '')
    const modeId = ref(store.modeId || 'narrative')
    const errMsg = ref('')
    const modes = ['narrative','briefing','instructional','pyramid','showcase']
    const modeLabels = { narrative:'叙事型', briefing:'简报型', instructional:'教学型', pyramid:'金字塔型', showcase:'展示型' }

    onMounted(async () => {
      try { styles.value = await api('GET', '/styles') || [] } catch (e) { errMsg.value = e.message }
      finally { loading.value = false }
    })
    function select(id) {
      styleId.value = id
      store.styleId = id
      const s = styles.value.find(x => x.id === id)
      if (s) { styleName.value = s.name_cn; store.styleName = s.name_cn }
    }
    async function confirmStyle() {
      if (!styleId.value) return
      if (!store.currentProject?.id) { errMsg.value = '请先打开项目'; return }
      store.modeId = modeId.value
      try {
        const r = await api('POST', '/projects/'+store.currentProject.id+'/style', { style_id: styleId.value, mode_id: modeId.value })
        store.designColors = r?.colors || {}
        store.designFonts = r?.fonts || {}
        showToast('风格已选择')
        router.push('/confirm')
      } catch (e) { errMsg.value = e.message }
    }
    return { loading, styles, styleId, styleName, modeId, modes, modeLabels, select, confirmStyle }
  }
}
</script>