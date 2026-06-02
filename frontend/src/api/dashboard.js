import request from '@/utils/request'

/**
 * 获取首页告警总览统计
 * @returns {Promise<{data: {reservoir_count:number, normal_count:number, abnormal_count:number, alert_count:number, offline_stations:number}}>}
 */
export function getDashboardOverview() {
  return request({
    method: 'get',
    url: '/v1/dashboard/overview'
  })
}

/**
 * 获取首页水库卡片列表（含核心指标最新值）
 * @returns {Promise<{data: Array}>}
 */
export function getReservoirOverviewList() {
  return request({
    method: 'get',
    url: '/v1/dashboard/reservoir-cards'
  })
}

/**
 * 获取最新告警列表
 * @param {{limit?:number}} params
 */
export function getLatestAlerts(params = {}) {
  return request({
    method: 'get',
    url: '/dashboard/alerts/latest',
    params
  })
}
