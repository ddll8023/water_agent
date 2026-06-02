import request from '@/utils/request'

/**
 * 获取预警列表（分页）
 * @param {Object} params - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页记录数
 * @param {number} [params.reservoir_id] - 水库 ID
 * @param {string} [params.alert_level] - 预警等级：info/warning/critical
 * @param {string} [params.status] - 状态：new/confirmed/processing/resolved
 * @param {string} [params.start_time] - 检出开始时间，格式 YYYY-MM-DD HH:mm:ss
 * @param {string} [params.end_time] - 检出结束时间，格式 YYYY-MM-DD HH:mm:ss
 * @returns {Promise} 预警分页数据
 */
export function getAlertList(params) {
  return request({
    method: 'get',
    url: '/v1/alerts',
    params
  })
}
