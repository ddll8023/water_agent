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
 * 单指标 24 小时趋势弹窗（已对接真实数据）
 * 功能描述：调取后端监测记录列表接口，获取指定站点+指标 24h 数据，渲染 ECharts 折线图
 * 依赖组件：无
 */
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
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
import { getMonitoringRecordsTrend } from '@/api/monitoring'
import { formatDateTime } from '@/utils/format'

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
  standardLimit: { type: [Number, null], default: null },
  reservoirId: { type: Number, default: undefined },
  stationId: { type: Number, default: undefined },
  indicatorId: { type: Number, default: undefined }
})

const emit = defineEmits(['update:modelValue'])

const chartRef = ref(null)
let chartInstance = null

const buildOption = (xAxisData, seriesData) => {
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
      data: xAxisData,
      axisLabel: { interval: 3, fontSize: 11, color: '#909399' }
    },
    yAxis: { type: 'value', name: props.indicatorName, scale: true },
    series: [
      {
        name: props.indicatorName,
        type: 'line',
        data: seriesData,
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

const fetchTrendData = async () => {
  if (!props.indicatorId) return { xAxis: [], series: [] }

  const now = new Date()
  const start = new Date(now.getTime() - 24 * 60 * 60 * 1000)

  try {
    const res = await getMonitoringRecordsTrend({
      reservoir_id: props.reservoirId || undefined,
      indicator_id: props.indicatorId,
      start_time: _formatDateTime(start),
      end_time: _formatDateTime(now)
    })
    const records = res.data?.lists || []
    records.sort(
      (a, b) => new Date(a.record_time).getTime() - new Date(b.record_time).getTime()
    )
    return {
      xAxis: records.map((r) => formatDateTime(r.record_time)),
      series: records.map((r) => r.value)
    }
  } catch {
    return { xAxis: [], series: [] }
  }
}

const _formatDateTime = (date) => {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

const handleOpen = async () => {
  nextTick(async () => {
    if (!chartRef.value) return
    if (!chartInstance) {
      chartInstance = echarts.init(chartRef.value)
    }
    const { xAxis, series } = await fetchTrendData()
    if (!xAxis.length) {
      ElMessage.info('该指标暂无趋势数据')
    }
    chartInstance.setOption(buildOption(xAxis, series), true)
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
