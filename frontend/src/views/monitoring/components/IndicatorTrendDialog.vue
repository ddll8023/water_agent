<template>
  <el-dialog
    :model-value="modelValue"
    width="700px"
    :close-on-click-modal="false"
    :title="`${indicatorName} · 近 24 小时趋势`"
    @update:model-value="(v) => emit('update:modelValue', v)"
    @open="handleOpen"
    @closed="handleClosed"
  >
    <div ref="chartRef" class="w-full h-[400px]" />
    <template #footer>
      <el-button @click="close">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
/**
 * 单指标 24 小时趋势弹窗
 * 功能描述：使用 ECharts 渲染 mock 24h 折线 + 标准限值虚线
 * 依赖组件：无
 */
import { ref, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
  TitleComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { generateHourlyTrend } from '../mock'

echarts.use([
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
  TitleComponent,
  CanvasRenderer
])

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  indicatorName: { type: String, default: 'pH' },
  standardLimit: { type: [Number, null], default: null }
})

const emit = defineEmits(['update:modelValue'])

const chartRef = ref(null)
let chartInstance = null

const buildOption = () => {
  const { xAxis, series } = generateHourlyTrend(1, 7, 1.5)
  const color = '#409EFF'
  const markLines = []
  if (props.standardLimit !== null && props.standardLimit !== undefined) {
    markLines.push({
      yAxis: props.standardLimit,
      name: `标准限值 ${props.standardLimit}`,
      lineStyle: { color: '#F56C6C', type: 'dashed', width: 1.2 },
      label: { formatter: `限值 ${props.standardLimit}`, color: '#F56C6C' }
    })
  }
  return {
    color: [color],
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: xAxis,
      axisLabel: { interval: 3, fontSize: 11, color: '#909399' }
    },
    yAxis: { type: 'value', name: props.indicatorName, scale: true },
    series: [
      {
        name: props.indicatorName,
        type: 'line',
        data: series,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2 },
        markLine: markLines.length
          ? { silent: true, symbol: 'none', data: markLines }
          : undefined
      }
    ]
  }
}

const handleOpen = () => {
  nextTick(() => {
    if (!chartRef.value) return
    if (!chartInstance) {
      chartInstance = echarts.init(chartRef.value)
    }
    chartInstance.setOption(buildOption(), true)
  })
}

const handleClosed = () => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

const close = () => emit('update:modelValue', false)
</script>
