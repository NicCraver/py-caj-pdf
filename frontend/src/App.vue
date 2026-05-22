<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { callApi } from './api.js'

const inputDir = ref('')
const outputDir = ref('')
const fileCount = ref(null)
const theme = ref('system')
const showHistory = ref(false)
const mutoolOk = ref(true)
const mutoolPath = ref('')

const progress = ref({
  state: 'idle',
  total: 0,
  completed: 0,
  success_count: 0,
  failed_count: 0,
  current_file: '',
  progress_percent: 0,
  logs: [],
  failed_files: [],
})

const history = ref([])
const historyDetail = ref(null)
const loadingHistory = ref(false)
const errorMsg = ref('')

const isRunning = computed(() => progress.value.state === 'running')
const isPaused = computed(() => progress.value.state === 'paused')
const isBusy = computed(() => ['running', 'paused'].includes(progress.value.state))
const isDone = computed(() => ['completed', 'cancelled'].includes(progress.value.state))

function applyTheme(value) {
  const root = document.documentElement
  if (value === 'dark') {
    root.classList.add('dark')
  } else if (value === 'light') {
    root.classList.remove('dark')
  } else {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    root.classList.toggle('dark', prefersDark)
  }
}

async function cycleTheme() {
  const order = ['light', 'dark', 'system']
  const next = order[(order.indexOf(theme.value) + 1) % order.length]
  theme.value = next
  applyTheme(next)
  await callApi('set_theme', next)
}

const themeLabel = computed(() => {
  if (theme.value === 'light') return '浅色'
  if (theme.value === 'dark') return '深色'
  return '跟随系统'
})

async function pickFolder(kind) {
  errorMsg.value = ''
  const res = await callApi('select_folder', kind)
  if (res.cancelled) return
  if (!res.ok) {
    errorMsg.value = res.error || '选择文件夹失败'
    return
  }
  if (kind === 'input') {
    inputDir.value = res.path
    await refreshScan()
  } else {
    outputDir.value = res.path
  }
}

async function refreshScan() {
  if (!inputDir.value) {
    fileCount.value = null
    return
  }
  const res = await callApi('scan_input', inputDir.value)
  if (res.ok) {
    fileCount.value = res.count
  } else {
    fileCount.value = null
    errorMsg.value = res.error
  }
}

async function startConversion() {
  errorMsg.value = ''
  const res = await callApi('start_conversion', inputDir.value, outputDir.value)
  if (!res.ok) {
    errorMsg.value = res.error || '无法开始转换'
  }
}

async function pauseConversion() {
  await callApi('pause_conversion')
}

async function resumeConversion() {
  await callApi('resume_conversion')
}

async function cancelConversion() {
  await callApi('cancel_conversion')
}

async function loadHistory() {
  loadingHistory.value = true
  try {
    history.value = await callApi('get_history', 50)
  } finally {
    loadingHistory.value = false
  }
}

async function openHistory() {
  showHistory.value = true
  historyDetail.value = null
  await loadHistory()
}

async function viewBatch(batchId) {
  const res = await callApi('get_history_detail', batchId)
  if (res.ok) {
    historyDetail.value = res
  }
}

function formatTime(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('zh-CN')
  } catch {
    return iso
  }
}

function statusText(state) {
  const map = {
    idle: '就绪',
    running: '转换中',
    paused: '已暂停',
    completed: '已完成',
    cancelled: '已取消',
  }
  return map[state] || state
}

function batchStatusText(status) {
  const map = {
    running: '进行中',
    completed: '已完成',
    cancelled: '已取消',
    interrupted: '已中断',
  }
  return map[status] || status
}

window.__onProgressUpdate = (payload) => {
  progress.value = payload
}

onMounted(async () => {
  try {
    const info = await callApi('get_app_info')
    mutoolOk.value = info.mutool_ok
    mutoolPath.value = info.mutool_path || ''
    const settings = await callApi('get_settings')
    theme.value = settings.theme || 'system'
    inputDir.value = settings.last_input_dir || ''
    outputDir.value = settings.last_output_dir || ''
    applyTheme(theme.value)
    if (inputDir.value) await refreshScan()
    progress.value = await callApi('get_progress')
  } catch (e) {
    errorMsg.value = e.message
  }
})

onUnmounted(() => {
  window.__onProgressUpdate = null
})
</script>

<template>
  <div class="flex h-full flex-col dark:bg-surface-dark">
    <!-- Header -->
    <header
      class="flex items-center justify-between border-b border-slate-200/80 px-6 py-4 dark:border-slate-800"
    >
      <div class="flex items-center gap-3">
        <div
          class="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10 text-accent"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.8"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <div>
          <h1 class="text-base font-semibold tracking-tight">CAJ 转 PDF</h1>
          <p class="text-xs text-slate-500 dark:text-slate-400">批量转换 · 队列处理</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button class="btn-secondary px-3 py-2 text-xs" @click="openHistory">历史记录</button>
        <button
          class="btn-secondary px-3 py-2 text-xs"
          :title="`当前: ${themeLabel}`"
          @click="cycleTheme"
        >
          {{ themeLabel }}
        </button>
      </div>
    </header>

    <!-- Mutool warning -->
    <div
      v-if="!mutoolOk"
      class="mx-6 mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200"
    >
      未检测到 mutool（MuPDF），部分 CAJ 格式将无法转换。请安装 MuPDF 或使用完整安装包。
    </div>

    <!-- Main -->
    <main class="flex-1 overflow-y-auto px-6 py-5">
      <div class="mx-auto max-w-2xl space-y-5">
        <!-- Folders -->
        <section class="card space-y-4">
          <div>
            <label class="mb-1.5 block text-xs font-medium text-slate-500 dark:text-slate-400">
              入口文件夹
            </label>
            <div class="flex gap-2">
              <input
                v-model="inputDir"
                class="input-field"
                placeholder="选择包含 CAJ 文件的文件夹（递归扫描）"
                readonly
              />
              <button class="btn-secondary shrink-0" :disabled="isBusy" @click="pickFolder('input')">
                浏览
              </button>
            </div>
            <p v-if="fileCount !== null" class="mt-1.5 text-xs text-slate-500">
              已发现 {{ fileCount }} 个 CAJ 文件
            </p>
          </div>

          <div>
            <label class="mb-1.5 block text-xs font-medium text-slate-500 dark:text-slate-400">
              出口文件夹
            </label>
            <div class="flex gap-2">
              <input
                v-model="outputDir"
                class="input-field"
                placeholder="PDF 将平铺保存到此文件夹"
                readonly
              />
              <button
                class="btn-secondary shrink-0"
                :disabled="isBusy"
                @click="pickFolder('output')"
              >
                浏览
              </button>
            </div>
          </div>
        </section>

        <!-- Progress -->
        <section class="card space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-medium">当前批次</h2>
            <span
              class="rounded-full px-2.5 py-0.5 text-xs font-medium"
              :class="{
                'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300':
                  progress.state === 'idle',
                'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300':
                  progress.state === 'running',
                'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300':
                  progress.state === 'paused',
                'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300':
                  progress.state === 'completed',
                'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300':
                  progress.state === 'cancelled',
              }"
            >
              {{ statusText(progress.state) }}
            </span>
          </div>

          <div class="grid grid-cols-3 gap-3 text-center">
            <div class="rounded-lg bg-slate-50 py-3 dark:bg-slate-800/50">
              <div class="text-lg font-semibold tabular-nums">{{ progress.total }}</div>
              <div class="text-xs text-slate-500">总计</div>
            </div>
            <div class="rounded-lg bg-slate-50 py-3 dark:bg-slate-800/50">
              <div class="text-lg font-semibold tabular-nums text-emerald-600 dark:text-emerald-400">
                {{ progress.success_count }}
              </div>
              <div class="text-xs text-slate-500">成功</div>
            </div>
            <div class="rounded-lg bg-slate-50 py-3 dark:bg-slate-800/50">
              <div class="text-lg font-semibold tabular-nums text-red-600 dark:text-red-400">
                {{ progress.failed_count }}
              </div>
              <div class="text-xs text-slate-500">失败</div>
            </div>
          </div>

          <div>
            <div class="mb-1.5 flex justify-between text-xs text-slate-500">
              <span v-if="progress.current_file">正在转换: {{ progress.current_file }}</span>
              <span v-else-if="isDone && progress.failed_count">
                完成，{{ progress.failed_count }} 个文件转换失败
              </span>
              <span v-else>进度</span>
              <span>{{ progress.progress_percent }}%</span>
            </div>
            <div class="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div
                class="h-full rounded-full bg-accent transition-all duration-300"
                :style="{ width: `${progress.progress_percent}%` }"
              />
            </div>
          </div>

          <div class="flex flex-wrap gap-2">
            <button
              class="btn-primary min-w-[120px]"
              :disabled="isBusy || !inputDir || !outputDir || fileCount === 0"
              @click="startConversion"
            >
              开始转换
            </button>
            <button v-if="isRunning" class="btn-secondary" @click="pauseConversion">暂停</button>
            <button v-if="isPaused" class="btn-secondary" @click="resumeConversion">继续</button>
            <button v-if="isBusy" class="btn-secondary text-red-600" @click="cancelConversion">
              取消
            </button>
          </div>

          <p v-if="errorMsg" class="text-sm text-red-600 dark:text-red-400">{{ errorMsg }}</p>
        </section>

        <!-- Logs -->
        <section class="card">
          <h2 class="mb-3 text-sm font-medium">实时日志</h2>
          <div
            class="max-h-48 overflow-y-auto rounded-lg bg-slate-50 p-3 font-mono text-xs leading-relaxed dark:bg-slate-900/50"
          >
            <p v-if="!progress.logs.length" class="text-slate-400">等待开始转换…</p>
            <p
              v-for="(log, i) in progress.logs"
              :key="i"
              :class="{
                'text-emerald-600 dark:text-emerald-400': log.level === 'success',
                'text-red-600 dark:text-red-400': log.level === 'error',
              }"
            >
              {{ log.message }}
            </p>
          </div>
        </section>
      </div>
    </main>

    <!-- History drawer -->
    <Teleport to="body">
      <div
        v-if="showHistory"
        class="fixed inset-0 z-50 flex justify-end bg-black/30 backdrop-blur-sm"
        @click.self="showHistory = false"
      >
        <aside
          class="flex h-full w-full max-w-md flex-col border-l border-slate-200 bg-white shadow-xl dark:border-slate-800 dark:bg-surface-cardDark"
        >
          <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h2 class="font-medium">转换历史</h2>
            <button class="btn-secondary px-2 py-1 text-xs" @click="showHistory = false">关闭</button>
          </div>

          <div v-if="historyDetail" class="flex-1 overflow-y-auto p-5">
            <button
              class="mb-4 text-xs text-accent hover:underline"
              @click="historyDetail = null"
            >
              ← 返回列表
            </button>
            <div class="mb-4 space-y-1 text-sm">
              <p><span class="text-slate-500">入口：</span>{{ historyDetail.batch.input_dir }}</p>
              <p><span class="text-slate-500">出口：</span>{{ historyDetail.batch.output_dir }}</p>
              <p>
                <span class="text-slate-500">时间：</span
                >{{ formatTime(historyDetail.batch.started_at) }}
              </p>
              <p>
                成功 {{ historyDetail.batch.success_count }} · 失败
                {{ historyDetail.batch.failed_count }}
              </p>
            </div>
            <ul class="space-y-2">
              <li
                v-for="item in historyDetail.items"
                :key="item.id"
                class="rounded-lg border border-slate-100 p-3 text-xs dark:border-slate-800"
              >
                <div class="flex items-start justify-between gap-2">
                  <span class="truncate font-medium">{{
                    item.source_path.split(/[/\\]/).pop()
                  }}</span>
                  <span
                    :class="
                      item.status === 'success'
                        ? 'text-emerald-600'
                        : 'text-red-600'
                    "
                  >
                    {{ item.status === 'success' ? '成功' : '失败' }}
                  </span>
                </div>
                <p v-if="item.error_msg" class="mt-1 text-red-500">{{ item.error_msg }}</p>
              </li>
            </ul>
          </div>

          <div v-else class="flex-1 overflow-y-auto p-5">
            <p v-if="loadingHistory" class="text-sm text-slate-500">加载中…</p>
            <p v-else-if="!history.length" class="text-sm text-slate-500">暂无历史记录</p>
            <ul v-else class="space-y-2">
              <li
                v-for="batch in history"
                :key="batch.id"
                class="cursor-pointer rounded-lg border border-slate-100 p-4 transition hover:border-accent/30 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                @click="viewBatch(batch.id)"
              >
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium">批次 #{{ batch.id }}</span>
                  <span class="text-xs text-slate-500">{{ batchStatusText(batch.status) }}</span>
                </div>
                <p class="mt-1 truncate text-xs text-slate-500">{{ batch.input_dir }}</p>
                <p class="mt-2 text-xs">
                  {{ formatTime(batch.started_at) }} · 共 {{ batch.total }} 个 · 成功
                  {{ batch.success_count }} · 失败 {{ batch.failed_count }}
                </p>
              </li>
            </ul>
          </div>
        </aside>
      </div>
    </Teleport>
  </div>
</template>
