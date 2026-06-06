export const NODE_STYLE = {
  Reservoir: { symbol: 'circle', color: '#0D9488', size: 35 },
  MonitoringStation: { symbol: 'diamond', color: '#10B981', size: 22 },
  River: { symbol: 'rect', color: '#60A5FA', size: 20 },
  Indicator: { symbol: 'triangle', color: '#8B5CF6', size: 18 },
  PollutionSource: {
    symbol: 'circle',
    colorByRisk: { 高: '#F56C6C', 中: '#E6A23C', 低: '#67C23A' },
    sizeByRisk: { 高: 28, 中: 24, 低: 20 },
    defaultColor: '#F56C6C',
    defaultSize: 24,
  },
}

export const EDGE_STYLE = {
  FLOWS_INTO: { type: 'solid', label: '注入' },
  UPSTREAM_OF: { type: 'dashed', label: '上游' },
  CORRELATED_WITH: { type: 'dotted', label: '相关' },
  MEASURES: { type: 'solid', label: '监测' },
  DISCHARGES_INTO: { type: 'solid', label: '排放' },
  BELONGS_TO: { type: 'solid', label: '属于' },
}

export const LEGEND_CONFIG = [
  { name: '水库', color: '#0D9488', symbol: 'circle' },
  { name: '监测站点', color: '#10B981', symbol: 'diamond' },
  { name: '河流', color: '#60A5FA', symbol: 'rect' },
  { name: '污染源', color: '#F56C6C', symbol: 'circle' },
  { name: '监测指标', color: '#8B5CF6', symbol: 'triangle' },
]
