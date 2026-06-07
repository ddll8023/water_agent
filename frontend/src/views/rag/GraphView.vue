<template>
  <div class="h-full flex flex-col bg-slate-900 relative">
    <div v-if="initialLoading" class="absolute inset-0 z-50 flex flex-col items-center justify-center bg-slate-900">
      <el-icon class="is-loading text-teal-400" :size="40"><Loading /></el-icon>
      <p class="mt-4 text-sm text-slate-400">正在加载图谱数据...</p>
    </div>
    <div v-if="loading && !initialLoading" class="absolute inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm transition-opacity duration-300">
      <el-icon class="is-loading text-teal-400" :size="28"><Loading /></el-icon>
      <span class="ml-3 text-sm text-slate-400">加载中...</span>
    </div>

    <header class="h-14 flex items-center gap-4 px-4 bg-slate-800/80 border-b border-slate-700 shrink-0">
      <h1 class="text-white font-semibold text-base whitespace-nowrap">水质知识图谱</h1>
      <el-autocomplete
        v-model="searchKeyword"
        :fetch-suggestions="handleSearch"
        placeholder="搜索水库/河流/污染源/指标..."
        :trigger-on-focus="false"
        clearable
        class="w-72"
        popper-class="graph-search-popper"
        @select="handleSelectNode"
      >
        <template #prefix>
          <el-icon class="text-slate-400"><Search /></el-icon>
        </template>
        <template #default="{ item }">
          <div class="flex items-center justify-between">
            <span>{{ item.name }}</span>
            <el-tag :type="tagType(item.type)" size="small">{{ item.type }}</el-tag>
          </div>
        </template>
      </el-autocomplete>
      <el-select
        v-model="reservoirCode"
        placeholder="水库筛选"
        clearable
        class="w-44"
        @change="loadData"
      >
        <el-option v-for="r in reservoirOptions" :key="r.code" :label="r.name" :value="r.code" />
      </el-select>
      <el-select
        v-model="watershedFilter"
        placeholder="流域筛选"
        clearable
        class="w-40"
        @change="handleWatershedChange"
      >
        <el-option
          v-for="ws in watershedOptions"
          :key="ws"
          :label="ws"
          :value="ws"
        />
      </el-select>
      <div class="ml-auto flex items-center gap-3 text-sm text-slate-400">
        <span>节点 <strong class="text-white">{{ nodeCount }}</strong></span>
        <span>关系 <strong class="text-white">{{ edgeCount }}</strong></span>
      </div>
    </header>

    <main ref="chartRef" class="flex-1 relative">
      <div
        v-if="!loading && !nodeCount"
        class="absolute inset-0 flex items-center justify-center text-slate-500"
      >
        <el-empty description="暂无图谱数据，请先导入基础数据" />
      </div>
    </main>

    <div class="absolute top-20 right-4 z-10 space-y-1">
      <div
        v-for="item in legendItems"
        :key="item.name"
        class="flex items-center gap-2 px-2 py-1 rounded cursor-pointer transition-colors"
        :class="legendVisible[item.name] ? 'bg-slate-700/60 text-slate-200' : 'bg-slate-800/40 text-slate-500 line-through'"
        @click="toggleLegend(item.name)"
      >
        <span
          class="inline-block w-3 h-3 rounded-full shrink-0"
          :style="{ backgroundColor: item.color }"
        />
        <span class="text-xs">{{ item.name }}</span>
      </div>
    </div>

    <div class="absolute bottom-6 left-1/2 -translate-x-1/2 z-10">
      <el-button-group class="backdrop-blur-sm bg-slate-800/60 rounded-lg border border-slate-700/40">
        <el-button size="small" :icon="Camera" @click="handleSnapshot">快照</el-button>
        <el-button size="small" :icon="Download" @click="handleExport">导出</el-button>
        <el-button size="small" :icon="Refresh" @click="handleReset">重置</el-button>
        <el-button size="small" :icon="ZoomOut" @click="handleFit">适配</el-button>
      </el-button-group>
    </div>

    <Transition name="panel-slide">
      <div
        v-if="drawerVisible && selectedNode"
        class="absolute top-14 right-2 bottom-2 w-80 z-20
               rounded-xl border border-slate-700/50
               bg-slate-900/90 backdrop-blur-xl
               flex flex-col overflow-hidden pointer-events-auto"
        @click.stop
      >
        <div class="flex items-center justify-between px-4 py-3 border-b border-slate-700/50 shrink-0">
          <h3 class="text-base font-semibold text-white truncate mr-2">{{ selectedNode.name }}</h3>
          <el-tag :type="tagType(selectedNode.type)" size="small" class="shrink-0">{{ selectedNode.type }}</el-tag>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-3">
          <div v-if="nodeDetailLoading" class="flex items-center justify-center py-8">
            <el-icon class="is-loading text-teal-400" :size="20"><Loading /></el-icon>
            <span class="ml-2 text-sm text-slate-400">加载详情中...</span>
          </div>
          <template v-else>
            <div
              v-for="(val, key) in nodeProperties"
              :key="key"
              class="flex justify-between items-start gap-2 text-sm"
            >
              <span class="text-slate-400 shrink-0">{{ key }}</span>
              <span class="text-slate-200 text-right break-all">{{ val ?? '-' }}</span>
            </div>
          </template>
          <el-divider class="!border-slate-700 !my-3" />
          <div class="flex flex-col gap-2">
            <el-button
              v-if="selectedNode.type === 'Reservoir'"
              type="primary"
              size="small"
              plain
              disabled
            >查看溯源路径</el-button>
            <el-button
              v-if="selectedNode.type === 'MonitoringStation'"
              type="primary"
              size="small"
              plain
              disabled
            >查看关联指标</el-button>
            <el-button
              type="primary"
              size="small"
              plain
              @click="handleExpandNode"
            >展开上下游</el-button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
/**
 * 知识图谱可视化（07g）
 * 功能描述：ECharts 力导向图展示水库/站点/河流/污染源/指标关联关系，支持搜索、筛选、详情查看
 * 依赖组件：ECharts GraphChart
 */
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Camera, Download, Refresh, ZoomOut, Loading } from '@element-plus/icons-vue'
import * as echarts from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import {
  TooltipComponent,
  TitleComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { getGraphOverview, searchNodes, expandNode, getNodeDetail } from '@/api/graph'
import { getReservoirOverviewList } from '@/api/dashboard'
import { NODE_STYLE, EDGE_STYLE, LEGEND_CONFIG } from './graphConfig'

echarts.use([GraphChart, TooltipComponent, TitleComponent, CanvasRenderer])

const chartRef = ref(null)
const loading = ref(true)
const initialLoading = ref(true)
const searchKeyword = ref('')
const reservoirCode = ref('')
const reservoirOptions = ref([])
const watershedFilter = ref('')
const drawerVisible = ref(false)
const selectedNode = ref(null)
const nodeDetail = ref(null)
const nodeDetailLoading = ref(false)

const allNodes = ref([])
const allEdges = ref([])
const chartInstance = ref(null)
const legendVisible = reactive(
  Object.fromEntries(LEGEND_CONFIG.map((item) => [item.name, true]))
)

const nodeCount = computed(() => allNodes.value.length)
const edgeCount = computed(() => allEdges.value.length)

const watershedOptions = computed(() => {
  const set = new Set()
  allNodes.value.forEach((n) => {
    if (n.watershed) set.add(n.watershed)
  })
  return [...set]
})

const nodeProperties = computed(() => {
  if (nodeDetail.value?.attributes && Object.keys(nodeDetail.value.attributes).length) {
    return nodeDetail.value.attributes
  }
  const n = selectedNode.value
  if (!n) return {}
  const props = { 名称: n.name, 类型: n.type }
  if (n.code) props.编号 = n.code
  if (n.watershed) props.流域 = n.watershed
  if (n.water_grade) props.水质等级 = n.water_grade
  if (n.risk_level) props.风险等级 = n.risk_level
  if (n.subtype) props.子类型 = n.subtype
  return props
})

const tagType = (type) => {
  const map = {
    Reservoir: '',
    MonitoringStation: 'success',
    River: 'info',
    PollutionSource: 'danger',
    Indicator: 'warning',
  }
  return map[type] || 'info'
}

function getNodeStyle(node) {
  const config = NODE_STYLE[node.type]
  if (!config) return { symbol: 'circle', color: '#94a3b8', size: 20 }
  if (node.type === 'PollutionSource') {
    const risk = node.risk_level
    return {
      symbol: config.symbol,
      color: config.colorByRisk[risk] || config.defaultColor,
      size: config.sizeByRisk[risk] || config.defaultSize,
    }
  }
  return { symbol: config.symbol, color: config.color, size: config.size }
}

function buildEChartsOption() {
  const showNodeTypes = new Set(
    LEGEND_CONFIG.filter((item) => legendVisible[item.name]).map((item) => {
      const map = { 水库: 'Reservoir', 监测站点: 'MonitoringStation', 河流: 'River', 污染源: 'PollutionSource', 监测指标: 'Indicator' }
      return map[item.name]
    })
  )

  const nodes = allNodes.value
    .filter((n) => showNodeTypes.has(n.type))
    .map((n) => {
      const style = getNodeStyle(n)
      const hexToRgba = (hex, alpha) => {
        const r = parseInt(hex.slice(1, 3), 16)
        const g = parseInt(hex.slice(3, 5), 16)
        const b = parseInt(hex.slice(5, 7), 16)
        return `rgba(${r},${g},${b},${alpha})`
      }
      return {
        id: n.id,
        name: n.name,
        value: n.type,
        category: n.type,
        symbol: style.symbol,
        itemStyle: { color: style.color, shadowBlur: 8, shadowColor: hexToRgba(style.color, 0.3) },
        symbolSize: style.size,
        watershed: n.watershed,
      }
    })

  const edges = allEdges.value
    .filter((e) => {
      const fromNode = allNodes.value.find((n) => n.id === e.source)
      const toNode = allNodes.value.find((n) => n.id === e.target)
      return fromNode && toNode && showNodeTypes.has(fromNode.type) && showNodeTypes.has(toNode.type)
    })
    .filter((e) => {
      if (!watershedFilter.value) return true
      const fromNode = allNodes.value.find((n) => n.id === e.source)
      return fromNode && fromNode.watershed === watershedFilter.value
    })
    .map((e) => {
      const style = EDGE_STYLE[e.relation] || { type: 'solid', label: e.relation }
      return {
        source: e.source,
        target: e.target,
        label: { show: true, formatter: style.label, fontSize: 10, color: '#94a3b8' },
        lineStyle: { type: style.type, color: '#475569', width: 1.5 },
      }
    })

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'node') {
          return `<strong>${params.name}</strong><br/>类型: ${params.value}`
        }
        return ''
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        force: {
          repulsion: 400,
          edgeLength: 150,
          gravity: 0.08,
          friction: 0.15,
        },
        roam: true,
        draggable: true,
        data: nodes,
        edges: edges,
        categories: LEGEND_CONFIG.map((item) => ({
          name: item.name,
          itemStyle: { color: item.color },
        })),
        label: {
          show: true,
          position: 'bottom',
          fontSize: 10,
          color: '#cbd5e1',
          formatter: (params) => params.name,
        },
        edgeLabel: {
          show: true,
          fontSize: 9,
          color: '#64748b',
          formatter: (p) => p.data?.label || '',
        },
        lineStyle: { color: '#475569', width: 1.5, curveness: 0.2 },
        emphasis: {
          focus: 'adjacency',
          itemStyle: { shadowBlur: 20, shadowColor: 'rgba(148,163,184,0.6)' },
          lineStyle: { width: 3, color: '#94a3b8' },
        },
        blur: {
          opacity: 0.1,
          lineStyle: { opacity: 0.1 },
        },
        zoom: 1,
      },
    ],
  }
}

async function renderGraph() {
  await nextTick()
  if (!chartRef.value) return
  if (!chartInstance.value) {
    chartInstance.value = echarts.init(chartRef.value)
  }
  const option = buildEChartsOption()
  chartInstance.value.setOption(option, true)
  chartInstance.value.on('click', async (params) => {
    if (params.dataType === 'node') {
      const node = allNodes.value.find((n) => n.id === params.data.id)
      if (node) {
        selectedNode.value = node
        nodeDetail.value = null
        drawerVisible.value = true
        const parts = node.id.split(':')
        if (parts.length >= 2) {
          nodeDetailLoading.value = true
          try {
            const res = await getNodeDetail(parts[0], parts.slice(1).join(':'))
            nodeDetail.value = res.data
          } catch {
            nodeDetail.value = null
          } finally {
            nodeDetailLoading.value = false
          }
        }
      }
    } else {
      drawerVisible.value = false
      chartInstance.value?.dispatchAction({ type: 'downplay' })
    }
  })
}

async function loadReservoirOptions() {
  try {
    const res = await getReservoirOverviewList()
    reservoirOptions.value = (res.data || []).map((r) => ({ code: r.code, name: r.name }))
  } catch {
    reservoirOptions.value = []
  }
}

async function loadData() {
  loading.value = true
  try {
    const res = await getGraphOverview(reservoirCode.value || undefined)
    allNodes.value = res.data?.nodes || []
    allEdges.value = res.data?.edges || []
  } catch {
    ElMessage.error('加载图谱数据失败')
  } finally {
    loading.value = false
    if (initialLoading.value) initialLoading.value = false
    await nextTick()
    renderGraph()
  }
}

async function handleSearch(query, cb) {
  if (!query || query.length < 1) {
    cb([])
    return
  }
  try {
    const res = await searchNodes(query)
    const items = (res.data?.node_list || []).map((item) => ({
      ...item,
      value: item.name,
    }))
    cb(items)
  } catch {
    cb([])
  }
}

function handleSelectNode(item) {
  const node = allNodes.value.find((n) => n.id === item.id)
  if (node && chartInstance.value) {
    selectedNode.value = node
    drawerVisible.value = true
    chartInstance.value.dispatchAction({
      type: 'highlight',
      seriesIndex: 0,
      dataIndex: allNodes.value.indexOf(node),
    })
  }
}

function handleWatershedChange() {
  renderGraph()
}

function toggleLegend(name) {
  legendVisible[name] = !legendVisible[name]
  renderGraph()
}

async function handleExpandNode() {
  if (!selectedNode.value) return
  const parts = selectedNode.value.id.split(':')
  if (parts.length < 2) return
  const type = parts[0]
  const id = parts.slice(1).join(':')

  const nodeIdx = allNodes.value.findIndex((n) => n.id === selectedNode.value.id)
  if (chartInstance.value && nodeIdx >= 0) {
    chartInstance.value.dispatchAction({ type: 'downplay' })
    chartInstance.value.dispatchAction({
      type: 'highlight',
      seriesIndex: 0,
      dataIndex: nodeIdx,
    })
  }

  try {
    const res = await expandNode(type, id)
    const newNodes = res.data?.nodes || []
    const newEdges = res.data?.edges || []
    const existingIds = new Set(allNodes.value.map((n) => n.id))
    const newIds = newNodes.filter((n) => !existingIds.has(n.id))
    if (newIds.length) {
      allNodes.value = [...allNodes.value, ...newIds]
      allEdges.value = [...allEdges.value, ...newEdges]
      renderGraph()
      ElMessage.success('已扩展 ' + newIds.length + ' 个关联节点')
    } else if (!newNodes.length) {
      ElMessage.info('该节点已无更多关联')
    } else {
      ElMessage.success('已高亮上下游关联节点')
    }
  } catch {
    ElMessage.error('扩展节点失败')
  }
}

function handleSnapshot() {
  if (!chartInstance.value) return
  try {
    const option = chartInstance.value.getOption()
    localStorage.setItem('graphSnapshot', JSON.stringify(option))
    ElMessage.success('快照已保存')
  } catch {
    ElMessage.warning('保存快照失败')
  }
}

function handleExport() {
  if (!chartInstance.value) return
  try {
    const url = chartInstance.value.getDataURL({ type: 'png' })
    const a = document.createElement('a')
    a.href = url
    a.download = `知识图谱_${new Date().toISOString().slice(0, 10)}.png`
    a.click()
    ElMessage.success('导出成功')
  } catch {
    ElMessage.warning('导出失败')
  }
}

function handleReset() {
  localStorage.removeItem('graphSnapshot')
  renderGraph()
  ElMessage.success('已重置视图')
}

function handleFit() {
  if (chartInstance.value) {
    chartInstance.value.dispatchAction({ type: 'restore' })
  }
}

onMounted(async () => {
  await loadReservoirOptions()
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
    chartInstance.value = null
  }
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  chartInstance.value?.resize()
}
</script>

<style scoped>
.panel-slide-enter-active,
.panel-slide-leave-active {
  transition: all 0.2s ease;
}
.panel-slide-enter-from,
.panel-slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
