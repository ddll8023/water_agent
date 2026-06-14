<template>
  <div>
    <el-breadcrumb separator="/" class="mb-4">
      <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item :to="{ path: '/alerts/list' }">预警中心</el-breadcrumb-item>
      <el-breadcrumb-item>预警详情</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="never" class="mb-4 !sticky !top-0 z-10">
      <div class="flex items-center justify-between">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-3 mb-2">
            <h2 class="text-xl font-semibold text-gray-900 truncate max-w-md">
              {{ alertDetail.title || '加载中...' }}
            </h2>
            <el-tag v-if="alertDetail.alert_level" :type="levelTagType" effect="dark" size="small">
              {{ levelLabel }}
            </el-tag>
            <el-tag v-if="alertDetail.status !== null" :type="statusTagType" size="small">
              {{ statusLabel }}
            </el-tag>
            <el-tag v-if="alertDetail.source === 1" type="warning" size="small">AI趋势分析</el-tag>
            <el-tag v-else-if="alertDetail.source === 0" type="info" size="small">规则预警</el-tag>
          </div>
          <div class="flex items-center gap-6 text-sm text-gray-500">
            <span class="flex items-center gap-1">
              <el-icon><Place /></el-icon>
              所属水库：{{ reservoirName || '-' }}
            </span>
            <span>检出时间：{{ formatDateTime(alertDetail.detected_at) }}</span>
            <span>持续时长：{{ durationText }}</span>
          </div>
        </div>
        <el-button-group class="flex-shrink-0 ml-4">
          <el-button
            :type="alertDetail.status === 0 ? 'warning' : 'default'"
            :disabled="alertDetail.status !== 0"
            :loading="confirmLoading"
            @click="handleConfirm"
          >确认预警</el-button>
          <el-button
            :type="alertDetail.status === 1 ? 'primary' : 'default'"
            :disabled="alertDetail.status !== 1"
            :loading="processLoading"
            @click="handleStartProcess"
          >开始处置</el-button>
          <el-button
            :type="alertDetail.status === 2 ? 'success' : 'default'"
            :disabled="alertDetail.status !== 2"
            :loading="resolveLoading"
            @click="handleResolve"
          >标记解决</el-button>
        </el-button-group>
      </div>
    </el-card>

    <div class="flex gap-4 mb-4">
      <div class="w-[55%]">
        <h3 class="text-base font-semibold text-gray-800 mb-3">超标指标</h3>
        <div v-if="detailLoading" class="space-y-3">
          <el-skeleton :rows="3" animated />
          <el-skeleton :rows="3" animated />
        </div>
        <el-alert
          v-else-if="detailError"
          title="加载超标指标失败"
          type="error"
          show-icon
          closable
          class="mb-3"
        >
          <template #action>
            <el-button size="small" @click="loadAlertDetail">重新加载</el-button>
          </template>
        </el-alert>
        <el-empty v-else-if="!indicators.length" description="所有指标均未超标" />
        <div v-else class="space-y-3">
          <el-card v-for="(item, idx) in indicators" :key="idx" shadow="never" class="indicator-card">
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-gray-800">{{ item.name }}</span>
              <span class="text-xs text-gray-400">标准限值：{{ item.limit }} {{ item.unit || '' }}</span>
            </div>
            <div class="flex items-baseline gap-3 mb-2">
              <span class="text-3xl font-bold text-gray-900">{{ item.value }}</span>
              <span class="text-sm text-red-500 font-medium">超标 {{ item.exceed_pct }}%</span>
            </div>
            <el-progress
              :percentage="Math.min(item.exceed_pct, 100)"
              :color="progressColor"
              :stroke-width="14"
              class="mb-2"
            />
            <div :ref="(el) => setSparklineRef(el, idx)" class="h-[60px] w-full rounded bg-gray-50" />
          </el-card>
        </div>
      </div>

      <div class="flex-1 min-w-0">
        <h3 class="text-base font-semibold text-gray-800 mb-3">溯源分析</h3>
        <div v-if="traceLoading">
          <el-skeleton :rows="6" animated class="mb-3" />
        </div>
        <el-alert
          v-else-if="traceError"
          title="加载溯源数据失败"
          type="error"
          show-icon
          closable
          class="mb-3"
        >
          <template #action>
            <el-button size="small" @click="loadTraceData">重新加载</el-button>
          </template>
        </el-alert>
        <el-empty v-else-if="!traceNodes.length" description="暂无溯源数据">
          <span class="text-xs text-gray-400">当前无法获取该预警的溯源图谱</span>
        </el-empty>
        <div v-else ref="graphRef" class="h-[360px] border border-gray-200 rounded-lg mb-3" />

        <h4 class="text-sm font-medium text-gray-700 mb-2">可能污染源列表</h4>
        <el-table
          :data="pollutionSources"
          border
          stripe
          size="small"
          class="w-full"
          @row-click="handleSourceRowClick"
        >
          <el-table-column prop="name" label="名称" min-width="110" />
          <el-table-column prop="distance" label="距离(km)" width="90" sortable />
          <el-table-column prop="risk_level" label="风险等级" width="95" sortable>
            <template #default="{ row }">
              <el-tag :type="riskLevelTagType(row.risk_level)" size="small">{{ row.risk_level }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="violations" label="历史违规次数" width="105" sortable />
          <template #empty>
            <el-empty description="暂无污染源数据" />
          </template>
        </el-table>
      </div>
    </div>

    <el-card shadow="never" class="mb-4" v-if="alertDetail.source_desc">
      <template #header>
        <div class="flex items-center gap-2">
          <span class="inline-flex items-center justify-center w-6 h-6 rounded-md bg-orange-50 text-orange-600">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </span>
          <span class="font-semibold text-gray-800">异常原因分析</span>
        </div>
      </template>
      <div class="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{{ alertDetail.source_desc }}</div>
    </el-card>

    <el-card shadow="never" class="mb-4">
      <template #header>
        <div class="flex items-center gap-2">
          <span class="inline-flex items-center justify-center w-6 h-6 rounded-md bg-teal-50 text-teal-600">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </span>
          <span class="font-semibold text-gray-800">AI 处置建议</span>
          <el-tag v-if="suggestionStatus === 2" type="warning" size="small">待确认</el-tag>
          <el-tag v-else-if="suggestionStatus === 3" type="success" size="small">已确认</el-tag>
          <el-tag v-else-if="suggestionStatus === 1" type="info" size="small">生成中</el-tag>
        </div>
      </template>
      <el-skeleton v-if="suggestionLoading" :rows="4" animated />
      <el-empty v-else-if="!suggestionSteps.length" description="暂无处置建议">
        <el-button type="primary" :loading="suggestionLoading" @click="handleGenerateSuggestion">
          生成处置建议
        </el-button>
      </el-empty>
      <div v-else class="space-y-5">
        <div
          v-for="(step, idx) in suggestionSteps"
          :key="idx"
          class="relative pl-14"
        >
          <div class="absolute left-0 top-0 w-10 h-10 rounded-full bg-teal-50 border-2 border-teal-400 flex items-center justify-center">
            <span class="text-sm font-bold text-teal-600">{{ String(step.step).padStart(2, '0') }}</span>
          </div>
          <div class="bg-white rounded-lg border border-gray-100 p-4 shadow-sm hover:shadow-md transition-shadow">
            <h4 class="text-base font-semibold text-gray-800 mb-2">{{ step.title }}</h4>
            <p class="text-sm text-gray-500 leading-relaxed">{{ step.description }}</p>
          </div>
        </div>
        <div class="flex gap-3">
          <el-button
            v-if="suggestionStatus !== 3"
            type="primary"
            class="flex-1"
            size="large"
            :loading="confirmSuggestionLoading"
            @click="handleConfirmSuggestion"
          >确认处置方案</el-button>
          <el-button
            class="flex-1"
            size="large"
            :loading="suggestionLoading"
            @click="handleGenerateSuggestion"
          >重新生成</el-button>
          <el-button
            class="flex-1"
            size="large"
            :loading="suggestionAdopting"
            @click="handleAdoptSuggestion"
          >采纳到备注</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="mb-4">
      <template #header>
        <span class="font-semibold text-gray-800">处置备注</span>
        <el-tag v-if="sortedNotes.length" size="small" type="info" class="ml-2">{{ sortedNotes.length }}条</el-tag>
      </template>

      <div v-if="sortedNotes.length" class="space-y-4 mb-4">
        <div
          v-for="note in sortedNotes"
          :key="note.id"
          class="flex gap-3 p-3 bg-gray-50 rounded-lg"
        >
          <el-avatar :size="32" class="!bg-blue-100 !text-blue-600 flex-shrink-0">
            <el-icon><User /></el-icon>
          </el-avatar>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-sm font-medium text-gray-700">用户 {{ note.user_id || '-' }}</span>
              <span class="text-xs text-gray-400">{{ formatDateTime(note.created_at) }}</span>
            </div>
            <div class="text-sm text-gray-600 whitespace-pre-wrap">{{ note.content }}</div>
          </div>
        </div>
      </div>

      <el-input
        v-model="noteContent"
        type="textarea"
        :rows="3"
        placeholder="请输入处置过程记录..."
        class="mb-3"
      />
      <el-button type="primary" :loading="noteSubmitting" @click="handleSubmitNote">提交备注</el-button>
    </el-card>

    <el-button
      class="fixed bottom-6 right-8 z-10"
      type="info"
      plain
      :icon="Clock"
      @click="handleOpenSimilar"
    >历史相似事件</el-button>

    <el-dialog v-model="drawerVisible" title="历史相似事件" width="420px" append-to-body top="5vh">
      <template #header>
        <div class="flex items-center gap-2">
          <span class="font-semibold">历史相似事件</span>
          <el-tag v-if="similarTotal" size="small" type="info">{{ similarTotal }}条</el-tag>
        </div>
      </template>

      <div class="min-h-[200px]">
        <el-skeleton v-if="similarLoading" :rows="8" animated />
        <el-empty v-else-if="!similarEvents.length" description="暂无相似历史预警" />
        <div v-else class="space-y-3">
          <el-card
            v-for="event in similarEvents"
            :key="event.id"
            shadow="never"
            class="!border !border-gray-100"
          >
            <div class="text-xs text-gray-400 mb-1">{{ formatDateTime(event.detected_at) }}</div>
            <div class="text-sm font-medium text-gray-800 mb-2">{{ event.title }}</div>
            <div class="flex flex-wrap gap-1 mb-2">
              <el-tag
                v-for="ind in (event.indicators || [])"
                :key="ind.name"
                size="small"
                :type="(event.matched_indicators || []).includes(ind.name) ? 'warning' : 'info'"
              >{{ ind.name }} {{ ind.value }}{{ ind.unit || '' }}</el-tag>
            </div>
            <div class="flex items-center justify-between text-xs text-gray-400">
              <span>已解决 {{ formatDateTime(event.resolved_at) }}</span>
              <el-tag size="small" type="success">已归档</el-tag>
            </div>
          </el-card>
        </div>
      </div>

      <template #footer>
        <div v-if="similarTotal > similarPageSize" class="flex justify-center">
          <el-pagination
            small
            layout="prev, pager, next"
            :total="similarTotal"
            :page-size="similarPageSize"
            v-model:current-page="similarPage"
            @current-change="loadSimilarData"
            background
          />
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 预警详情与溯源
 * 功能描述：预警详情查看、超标指标展示、溯源图谱、AI处置建议、状态流转、处置备注
 * 依赖组件：ECharts
 */
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Place, Clock, User } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/format'
import { getAlertDetail, updateAlert, submitAlertNote, getAlertTrace, generateSuggestion, getSimilarEvents, confirmSuggestion } from '@/api/alert'
import { getReservoirList } from '@/api/reservoir'
import { useAuthStore } from '@/stores/auth'
import * as echarts from 'echarts/core'
import { LineChart, GraphChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  TitleComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, GraphChart, GridComponent, TooltipComponent, TitleComponent, CanvasRenderer])

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const alertDetail = reactive({
  id: null,
  reservoir_id: null,
  handler_id: null,
  title: '',
  alert_level: '',
  indicators: [],
  source_desc: '',
  suggestion: '',
  status: null,
  detected_at: null,
  resolved_at: null,
  created_at: null,
  notes: []
})

const reservoirName = ref('')
const reservoirMap = ref({})

const detailLoading = ref(true)
const detailError = ref(false)

const traceLoading = ref(true)
const traceError = ref(false)
const traceNodes = ref([])
const traceEdges = ref([])

const suggestionLoading = ref(false)
const suggestionSteps = ref([])
const suggestionAdopting = ref(false)
const suggestionStatus = ref(0)
const confirmSuggestionLoading = ref(false)

const similarLoading = ref(true)
const similarEvents = ref([])
const similarPage = ref(1)
const similarPageSize = ref(10)
const similarTotal = ref(0)

const confirmLoading = ref(false)
const processLoading = ref(false)
const resolveLoading = ref(false)

const pollutionSources = ref([])
const noteContent = ref('')
const noteSubmitting = ref(false)
const drawerVisible = ref(false)

const graphRef = ref(null)
const graphInstance = ref(null)
const sparklineInstances = ref([])
const sparklineRefMap = new Map()

const levelLabel = computed(() => {
  const map = { 1: '注意', 2: '警告', 3: '严重' }
  const level = alertDetail.alert_level
  return map[level] ?? map[Number(level)] ?? level
})

const levelTagType = computed(() => {
  const map = { 1: 'info', 2: 'warning', 3: 'danger' }
  const level = alertDetail.alert_level
  return map[level] ?? map[Number(level)] ?? 'info'
})

const statusLabel = computed(() => {
  const map = { 0: '待确认', 1: '处置中', 2: '处置中', 3: '已解决' }
  return map[alertDetail.status] || alertDetail.status
})

const statusTagType = computed(() => {
  const map = { 0: '', 1: 'warning', 2: 'primary', 3: 'success' }
  return map[alertDetail.status] || 'info'
})

const durationText = computed(() => {
  if (!alertDetail.detected_at) return '-'
  const start = new Date(alertDetail.detected_at).getTime()
  const end = alertDetail.resolved_at ? new Date(alertDetail.resolved_at).getTime() : Date.now()
  const diff = end - start
  if (diff <= 0) return '不足1分钟'
  const hours = Math.floor(diff / 3600000)
  const minutes = Math.floor((diff % 3600000) / 60000)
  if (hours > 0) return `${hours}小时${minutes}分钟`
  return `${minutes}分钟`
})

const sortedNotes = computed(() => {
  const list = alertDetail.notes || []
  return [...list].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
})

const indicators = computed(() => {
  const list = alertDetail.indicators || []
  return list.map((item) => {
    const value = parseFloat(item.value) || 0
    const limit = parseFloat(item.limit) || 1
    const exceedPct = limit > 0 ? Math.round(((value - limit) / limit) * 100) : 0
    return { ...item, value, limit, exceed_pct: Math.max(exceedPct, 0) }
  })
})

const progressColor = (percentage) => {
  if (percentage <= 30) return '#e6a23c'
  if (percentage <= 60) return '#f56c6c'
  return '#dd3333'
}

const riskLevelTagType = (level) => {
  const map = { 高: 'danger', 中: 'warning', 低: 'info' }
  return map[level] || 'info'
}

function setSparklineRef(el, idx) {
  if (el) {
    sparklineRefMap.set(idx, el)
  }
}

const fetchReservoirNames = async () => {
  try {
    const res = await getReservoirList({ page: 1, page_size: 9999 })
    const list = res.data.lists || []
    const map = {}
    list.forEach((r) => { map[r.id] = r.name })
    reservoirMap.value = map
    reservoirName.value = map[alertDetail.reservoir_id] || ''
  } catch {
    reservoirName.value = `ID:${alertDetail.reservoir_id}`
  }
}

const loadAlertDetail = async () => {
  const id = Number(route.params.id)
  if (!id) {
    ElMessage.error('预警ID无效')
    detailLoading.value = false
    return
  }

  detailLoading.value = true
  detailError.value = false
  alertDetail.id = id

  try {
    const res = await getAlertDetail(id)
    const data = res.data
    if (data) {
      Object.assign(alertDetail, data)
    }
    reservoirName.value = reservoirMap.value[alertDetail.reservoir_id] || ''
    await fetchReservoirNames()
    await nextTick()
    initSparklines()
  } catch (e) {
    detailError.value = true
    ElMessage.error(e.message || '获取预警详情失败')
  } finally {
    detailLoading.value = false
  }
}

const initSparklines = () => {
  sparklineInstances.value.forEach((inst) => inst.dispose())
  sparklineInstances.value = []

  indicators.value.forEach((item, idx) => {
    const el = sparklineRefMap.get(idx)
    if (!el) return

    const readings = item.readings && item.readings.length
      ? item.readings
      : Array.from({ length: 24 }, () => +(item.limit * (0.8 + Math.random() * 0.4)).toFixed(3))

    const chart = echarts.init(el)
    chart.setOption({
      grid: { left: 2, right: 2, top: 4, bottom: 2 },
      xAxis: { type: 'category', show: false, data: readings.map((_, i) => i) },
      yAxis: { type: 'value', show: false, min: Math.min(...readings) * 0.9 },
      series: [{
        type: 'line',
        data: readings,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#f56c6c' },
        areaStyle: { color: 'rgba(245,108,108,0.15)' }
      }],
      tooltip: { trigger: 'axis', formatter: (params) => `数值: ${params[0].value}` }
    })
    sparklineInstances.value.push(chart)
  })
}

const initTraceGraph = () => {
  if (graphInstance.value) graphInstance.value.dispose()
  const el = graphRef.value
  if (!el || !traceNodes.value.length) return

  const chart = echarts.init(el)

  const colors = {
    Reservoir: '#409eff',
    River: '#67c23a',
    PollutionSource: '#f56c6c'
  }

  const nodes = traceNodes.value.map(n => ({
    id: n.id,
    name: n.name,
    symbolSize: n.type === 'Reservoir' ? 40 : n.type === 'PollutionSource' ? 32 : 28,
    itemStyle: { color: colors[n.type] || '#999' },
    category: n.type
  }))

  const edges = traceEdges.value.map(e => ({
    source: e.source,
    target: e.target,
    label: { show: true, formatter: e.relation, fontSize: 10 }
  }))

  chart.setOption({
    tooltip: {
      formatter: p => `<b>${p.data.name}</b><br/>类型: ${p.data.category}`
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      edges: edges,
      roam: true,
      draggable: true,
      force: { repulsion: 400, edgeLength: 150 },
      categories: ['Reservoir', 'River', 'PollutionSource'].map(t => ({ name: t })),
      label: { show: true, position: 'bottom', fontSize: 11 },
      lineStyle: { color: 'source', curveness: 0.3, width: 2 }
    }]
  })

  graphInstance.value = chart
}

const loadTraceData = async () => {
  traceLoading.value = true
  traceError.value = false
  try {
    const res = await getAlertTrace(alertDetail.id)
    const data = res.data
    traceNodes.value = data.nodes || []
    traceEdges.value = data.edges || []
    pollutionSources.value = (data.sources || []).map(s => ({
      id: s.id,
      name: s.name,
      distance: s.distance_km,
      risk_level: s.risk_level,
      violations: s.violation_count
    }))
    traceLoading.value = false
    await nextTick()
    initTraceGraph()
  } catch (e) {
    traceError.value = true
    console.error('溯源数据加载失败:', e)
    traceLoading.value = false
  }
}

const loadSuggestionData = () => {
  suggestionStatus.value = alertDetail.suggestion_status ?? 0
  try {
    if (!alertDetail.suggestion) {
      suggestionSteps.value = []
      return
    }
    if (Array.isArray(alertDetail.suggestion)) {
      suggestionSteps.value = alertDetail.suggestion
    } else {
      const parsed = JSON.parse(alertDetail.suggestion)
      suggestionSteps.value = Array.isArray(parsed) ? parsed : []
    }
  } catch {
    suggestionSteps.value = []
  } finally {
    suggestionLoading.value = false
  }
}

const handleGenerateSuggestion = async () => {
  suggestionLoading.value = true
  try {
    const res = await generateSuggestion(alertDetail.id)
    suggestionSteps.value = res.data?.lists || []
    suggestionStatus.value = 2
    await loadAlertDetail()
  } catch (e) {
    ElMessage.error('生成处置建议失败')
    console.error(e)
  } finally {
    suggestionLoading.value = false
  }
}

const handleConfirmSuggestion = async () => {
  confirmSuggestionLoading.value = true
  try {
    await confirmSuggestion(alertDetail.id)
    suggestionStatus.value = 3
    ElMessage.success('处置方案已确认')
  } catch (e) {
    ElMessage.error(e.message || '确认失败')
  } finally {
    confirmSuggestionLoading.value = false
  }
}

const loadSimilarData = async () => {
  similarLoading.value = true
  try {
    const res = await getSimilarEvents(alertDetail.id, {
      page: similarPage.value,
      page_size: similarPageSize.value
    })
    const data = res.data
    similarEvents.value = data.lists || []
    similarTotal.value = data.pagination?.total || 0
  } catch (e) {
    similarEvents.value = []
    console.error('加载历史相似事件失败:', e)
  } finally {
    similarLoading.value = false
  }
}

const handleOpenSimilar = async () => {
  drawerVisible.value = true
  if (!similarEvents.value.length) {
    await loadSimilarData()
  }
}

const callUpdateAlert = async (status) => {
  const id = alertDetail.id
  if (!id) {
    ElMessage.error('预警ID无效')
    return
  }
  const data = { status, handler_id: authStore.userInfo?.user_id || null }
  const res = await updateAlert(id, data)
  if (res && res.data) {
    Object.assign(alertDetail, res.data)
  }
}

const handleConfirm = async () => {
  try {
    await ElMessageBox.confirm('确认该预警信息无误？', '确认预警', { type: 'warning' })
    confirmLoading.value = true
    await callUpdateAlert(1)
    ElMessage.success('预警已确认')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '确认预警失败')
    }
  } finally {
    confirmLoading.value = false
  }
}

const handleStartProcess = async () => {
  try {
    await ElMessageBox.confirm('开始处置该预警？', '开始处置', { type: 'info' })
    processLoading.value = true
    await callUpdateAlert(2)
    ElMessage.success('已开始处置')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '开始处置失败')
    }
  } finally {
    processLoading.value = false
  }
}

const handleResolve = async () => {
  try {
    await ElMessageBox.confirm('确认该预警已解决？', '标记解决', { type: 'success' })
    resolveLoading.value = true
    await callUpdateAlert(3)
    ElMessage.success('预警已标记为已解决')
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '标记解决失败')
    }
  } finally {
    resolveLoading.value = false
  }
}

const handleAdoptSuggestion = async () => {
  suggestionAdopting.value = true
  await new Promise((r) => setTimeout(r, 300))
  const text = suggestionSteps.value.map((s, i) => `${i + 1}. ${s.title}：${s.description}`).join('\n')
  noteContent.value = noteContent.value
    ? noteContent.value + '\n---\n' + text
    : text
  suggestionAdopting.value = false
  ElMessage.success('方案已写入处置备注')
}

const handleSubmitNote = async () => {
  if (!noteContent.value.trim()) {
    ElMessage.warning('请输入备注内容')
    return
  }
  noteSubmitting.value = true
  try {
    const res = await submitAlertNote(alertDetail.id, noteContent.value.trim())
    if (res?.data) {
      if (!alertDetail.notes) alertDetail.notes = []
      alertDetail.notes.push(res.data)
    }
    ElMessage.success('备注已提交')
    noteContent.value = ''
  } catch (e) {
    ElMessage.error(e.message || '提交备注失败')
  } finally {
    noteSubmitting.value = false
  }
}

const handleSourceRowClick = (row) => {
  if (!graphInstance.value) return
  const idx = traceNodes.value.findIndex(n => n.id === row.id)
  if (idx === -1) return
  graphInstance.value.dispatchAction({
    type: 'highlight',
    seriesIndex: 0,
    dataIndex: idx
  })
}

const handleResize = () => {
  graphInstance.value?.resize()
}

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  await Promise.all([
    loadAlertDetail(),
    loadTraceData()
  ])
  loadSuggestionData()
})

onBeforeUnmount(() => {
  sparklineInstances.value.forEach((inst) => inst.dispose())
  if (graphInstance.value) {
    graphInstance.value.dispose()
  }
  window.removeEventListener('resize', handleResize)
})
</script>
