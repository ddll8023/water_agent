/**
 * 监测详情页占位数据
 * 仅用于前端 UI 展示与 ECharts 渲染，后端对接时移除
 */

export const INDICATOR_LIST = [
  { id: 1, name: 'pH', code: 'PH', unit: '', category: '化学', standardLimit: 9.0 },
  { id: 2, name: '溶解氧', code: 'DO', unit: 'mg/L', category: '化学', standardLimit: 5.0 },
  { id: 3, name: 'COD', code: 'COD', unit: 'mg/L', category: '化学', standardLimit: 20 },
  { id: 4, name: '氨氮', code: 'NH3N', unit: 'mg/L', category: '化学', standardLimit: 1.0 },
  { id: 5, name: '总磷', code: 'TP', unit: 'mg/L', category: '化学', standardLimit: 0.2 },
  { id: 6, name: '总氮', code: 'TN', unit: 'mg/L', category: '化学', standardLimit: 1.0 },
  { id: 7, name: '高锰酸盐指数', code: 'CODMn', unit: 'mg/L', category: '化学', standardLimit: 6 },
  { id: 8, name: '水温', code: 'SWT', unit: '℃', category: '物理', standardLimit: null },
  { id: 9, name: '浊度', code: 'ZD', unit: 'NTU', category: '物理', standardLimit: null }
]

export const INDICATOR_COLOR_PALETTE = [
  '#409EFF',
  '#67C23A',
  '#E6A23C',
  '#F56C6C',
  '#909399',
  '#9b59b6',
  '#16a085',
  '#e67e22',
  '#34495e'
]

export const STATION_TYPE_LABELS = {
  auto: '自动站',
  manual: '人工站',
  sensing: '遥感站'
}

export const STATION_TYPE_TAG = {
  auto: 'success',
  manual: 'warning',
  sensing: 'info'
}

const pad = (n) => String(n).padStart(2, '0')

const formatDateTime = (date) =>
  `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(
    date.getMinutes()
  )}:${pad(date.getSeconds())}`

const formatDate = (date) =>
  `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`

/**
 * 生成指定天数、每小时一个点的伪随机趋势数据
 * @param {number} days
 * @param {number} base
 * @param {number} amplitude
 * @returns {{ xAxis: string[], series: number[] }}
 */
export const generateHourlyTrend = (days = 1, base = 7, amplitude = 2) => {
  const pointCount = days * 24
  const now = new Date()
  const xAxis = []
  const series = []
  for (let i = pointCount - 1; i >= 0; i--) {
    const d = new Date(now.getTime() - i * 60 * 60 * 1000)
    xAxis.push(formatDateTime(d))
    const value = base + Math.sin(i / 6) * amplitude + (Math.random() - 0.5) * amplitude * 0.4
    series.push(Number(value.toFixed(3)))
  }
  return { xAxis, series }
}

/**
 * 生成按天聚合的趋势数据，用于 Tab2 大图
 * @param {number} days
 * @param {number} base
 * @param {number} amplitude
 */
export const generateDailyTrend = (days = 7, base = 7, amplitude = 2) => {
  const now = new Date()
  const xAxis = []
  const series = []
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
    xAxis.push(formatDate(d))
    const value = base + Math.sin(i / 2) * amplitude + (Math.random() - 0.5) * amplitude * 0.3
    series.push(Number(value.toFixed(3)))
  }
  return { xAxis, series }
}
