import { reactive } from 'vue'

export const store = reactive({
  pageTitle: '',
  currentProject: null,
  projects: [],
  slides: [],
  styles: [],
  styleId: '',
  styleName: '',
  modeId: 'narrative',
  designColors: {},
  designFonts: {},
  topicText: '',
  hasTopic: false,
  toast: { show: false, msg: '', type: 'success' },
  // Progress
  taskId: '',
  progressPct: 0,
  progressText: '准备中...',
  taskSteps: [],
  taskDone: false,
  taskError: '',
  downloadUrl: '',
})