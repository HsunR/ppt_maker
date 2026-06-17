<template>
  <span :class="['status-badge', status]">{{ label }}</span>
</template>

<script>
export default {
  props: { status: String },
  computed: {
    label() {
      const map = { created:'已创建', sourcing:'内容输入', outlining:'大纲编辑', styling:'选风格',
                    ready:'待生成', generating:'生成中', done:'已完成', failed:'失败' }
      return map[this.status] || this.status
    }
  }
}
</script>