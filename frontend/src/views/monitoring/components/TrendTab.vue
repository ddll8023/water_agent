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
        >
          <el-option
            v-for="item in INDICATOR_LIST"
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
        <span class="text-sm text-gray-700">历史趋势（mock 数据）</span>
      </template>
      <div ref="chartRef" class="w-full h-[400px]" />
    </el-card>
  </div>
</template>

<script setup>
/**
 * 历史趋势 Tab
 * 功能描述：日期范围 + 指标多选 + ECharts 折线图（多指标叠加 + 标准限值虚线）
 * 依赖组件：无
 */
import { ref, reactive, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
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
import { INDICATOR_LIST, INDICATOR_COLOR_PALETTE, generateDailyTrend } from '../mock'

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
const selectedIndicators = ref([1, 2, 3])

const chartRef = ref(null)
let chartInstance = null
let resizeHandler = null

const buildSeries = (indicatorIds) => {
  return indicatorIds.map((id, index) => {
    const meta = INDICATOR_LIST.find((i) => i.id === id) || INDICATOR_LIST[0]
    const color = INDICATOR_COLOR_PALETTE[index % INDICATOR_COLOR_PALETTE.length]
    const { series } = generateDailyTrend(7, index + 5, 1.2)
    const markLines = []
    if (meta.standardLimit !== null && meta.standardLimit !== undefined) {
      markLines.push({
        yAxis: meta.standardLimit,
        name: `${meta.name}限值`,
        lineStyle: { color, type: 'dashed', width: 1 },
        label: { formatter: `${meta.name}限值 ${meta.standardLimit}`, color }
      })
    }
    return {
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
    }
  })
}

const renderChart = () => {
  if (!chartRef.value) return
  const { xAxis } = generateDailyTrend(7, 5, 1.2)
  const ids = selectedIndicators.value.length ? selectedIndicators.value : [1]
  const option = {
    color: INDICATOR_COLOR_PALETTE,
    tooltip: { trigger: 'axis' },
    legend: { top: 0, type: 'scroll' },
    grid: { left: 50, right: 20, top: 40, bottom: 60 },
    xAxis: { type: 'category', data: xAxis, boundaryGap: false },
    yAxis: { type: 'value', scale: true, name: '监测值' },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', height: 20, bottom: 10 }
    ],
    series: buildSeries(ids)
  }
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  } else {
    chartInstance.clear()
  }
  chartInstance.setOption(option, true)
}

const handleQuery = () => {
  renderChart()
}

const handleReset = () => {
  timeRange.value = null
  selectedIndicators.value = [1, 2, 3]
  renderChart()
}

watch(
  () => selectedIndicators.value,
  () => nextTick(renderChart)
)

onMounted(() => {
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
