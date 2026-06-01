import request from '@/utils/request'

/**
 * 获取监测记录列表（分页）
 * @param {Object} params - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页记录数
 * @param {number} [params.reservoir_id] - 水库 ID
 * @param {number} [params.station_id] - 站点 ID
 * @param {number} [params.indicator_id] - 指标 ID
 * @param {string} [params.start_time] - 开始时间，格式 YYYY-MM-DD HH:mm:ss
 * @param {string} [params.end_time] - 结束时间，格式 YYYY-MM-DD HH:mm:ss
 * @param {number} [params.quality_flag] - 数据质量标志：0 可疑 1 正常 2 无效
 * @returns {Promise} 监测记录分页数据
 */
export function getMonitoringRecordsList(params) {
  return request({
    method: 'get',
    url: '/monitoring/records',
    params
  })
}
