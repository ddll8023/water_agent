<template>
  <div>
    <el-card shadow="never" class="mb-4">
      <div class="flex items-center flex-wrap gap-3">
        <el-date-picker
          v-model="timeRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          value-format="YYYY-MM-DD HH:mm:ss"
          :shortcuts="shortcuts"
          class="!w-96"
        />
        <el-select
          v-model="selectedIndicators"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择指标"
          class="!w-80"
          @change="handleIndicatorChange"
        >
          <el-option
            v-for="item in indicatorOptions"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-button type="primary" @click="handleQuery">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
        <el-button @click="handleReset">
          <el-icon><RefreshLeft /></el-icon>
          重置
        </el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <span class="text-sm text-gray-700">历史趋势</span>
      </template>
      <div ref="chartRef" class="w-full h-[400px]" />
    </el-card>
  </div>
</template>

<script setup>
/**
 * 历史趋势 Tab（已对接真实数据）
 * 功能描述：日期范围 + 指标多选 + ECharts 折线图，调取监测记录列表接口渲染多指标趋势
 * 依赖组件：无
 */
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, RefreshLeft } from '@element-plus/icons-vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
  TitleComponent,
  DataZoomComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { getMonitoringRecordsTrend } from '@/api/monitoring'
import { getIndicatorList } from '@/api/indicator'

echarts.use([
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
  TitleComponent,
  DataZoomComponent,
  CanvasRenderer
])

const route = useRoute()
const reservoirId = Number(route.params.id)

const shortcuts = [
  {
    text: '最近 24 小时',
    value: () => {
      const end = new Date()
      const start = new Date(end.getTime() - 24 * 60 * 60 * 1000)
      return [start, end]
    }
  },
  {
    text: '最近 7 天',
    value: () => {
      const end = new Date()
      const start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000)
      return [start, end]
    }
  },
  {
    text: '最近 30 天',
    value: () => {
      const end = new Date()
      const start = new Date(end.getTime() - 30 * 24 * 60 * 60 * 1000)
      return [start, end]
    }
  }
]

const timeRange = ref(null)
const selectedIndicators = ref([])
const indicatorOptions = ref([])
const indicatorMap = ref({})

const chartRef = ref(null)
let chartInstance = null
let resizeHandler = null

const INDICATOR_COLOR_PALETTE = [
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399',
  '#9b59b6', '#16a085', '#e67e22', '#34495e'
]

const fetchTrendData = async (indicatorId, startTime, endTime) => {
  try {
    const res = await getMonitoringRecordsTrend({
      reservoir_id: reservoirId || undefined,
      indicator_id: indicatorId,
      start_time: startTime,
      end_time: endTime
    })
    const records = res.data?.lists || []
    records.sort(
      (a, b) => new Date(a.record_time).getTime() - new Date(b.record_time).getTime()
    )
    return {
      xAxis: records.map((r) => r.record_time),
      series: records.map((r) => r.value)
    }
  } catch {
    return { xAxis: [], series: [] }
  }
}

const renderChart = async () => {
  if (!chartRef.value) return

  const startTime = timeRange.value?.[0]
  const endTime = timeRange.value?.[1]
  const ids = selectedIndicators.value.length ? selectedIndicators.value : []

  // 收集所有选中指标的数据
  const allSeries = []
  let allXAxis = []

  for (let i = 0; i < ids.length; i++) {
    const meta = indicatorMap.value[ids[i]]
    if (!meta) continue
    const color = INDICATOR_COLOR_PALETTE[i % INDICATOR_COLOR_PALETTE.length]
    const { xAxis, series } = await fetchTrendData(ids[i], startTime, endTime)
    if (xAxis.length) {
      allXAxis = xAxis
    }
    const markLines = []
    const limit = _getLimit(meta)
    if (limit !== null) {
      markLines.push({
        yAxis: limit,
        name: `${meta.name}限值`,
        lineStyle: { color, type: 'dashed', width: 1 },
        label: { formatter: `${meta.name}限值 ${limit}`, color }
      })
    }
    allSeries.push({
      name: meta.name,
      type: 'line',
      data: series,
      smooth: true,
      symbol: 'circle',
      symbolSize: 5,
      lineStyle: { width: 2, color },
      itemStyle: { color },
      markLine: markLines.length
        ? { silent: true, symbol: 'none', data: markLines }
        : undefined
    })
  }

  const option = {
    tooltip: { trigger: 'axis' },
    legend: { top: 0, type: 'scroll' },
    grid: { left: 50, right: 20, top: 40, bottom: 60 },
    xAxis: {
      type: 'category',
      data: allXAxis,
      boundaryGap: false,
      axisLabel: { fontSize: 11, color: '#909399' }
    },
    yAxis: { type: 'value', scale: true, name: '监测值' },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', height: 20, bottom: 10 }
    ],
    series: allSeries.length
      ? allSeries
      : [{ name: '暂无数据', type: 'line', data: [] }]
  }

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  } else {
    chartInstance.clear()
  }
  chartInstance.setOption(option, true)
}

const _getLimit = (indicator) => {
  const limits = [
    indicator.standard_limit_i,
    indicator.standard_limit_ii,
    indicator.standard_limit_iii,
    indicator.standard_limit_iv,
    indicator.standard_limit_v
  ].filter((v) => v !== null && v !== undefined)
  return limits.length ? Math.max(...limits) : null
}

const fetchIndicatorOptions = async () => {
  try {
    const res = await getIndicatorList({ page: 1, page_size: 9999 })
    const list = res.data?.lists || []
    indicatorOptions.value = list
    const map = {}
    list.forEach((item) => {
      map[item.id] = item
    })
    indicatorMap.value = map
    // 默认选中前 3 个指标
    selectedIndicators.value = list.slice(0, 3).map((i) => i.id)
  } catch {
    indicatorOptions.value = []
  }
}

const handleQuery = () => {
  nextTick(renderChart)
}

const handleIndicatorChange = () => {
  nextTick(renderChart)
}

const handleReset = () => {
  timeRange.value = null
  selectedIndicators.value = indicatorOptions.value.slice(0, 3).map((i) => i.id)
  nextTick(renderChart)
}

onMounted(async () => {
  await fetchIndicatorOptions()
  nextTick(() => {
    renderChart()
    resizeHandler = () => chartInstance && chartInstance.resize()
    window.addEventListener('resize', resizeHandler)
  })
})

onBeforeUnmount(() => {
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    resizeHandler = null
  }
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>
