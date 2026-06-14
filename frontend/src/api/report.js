import request from '@/utils/request'

/**
 * 获取报告列表（分页）
 * @param {Object} params - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页记录数
 * @param {string} [params.type] - 报告类型：daily/quarterly/event
 * @param {string} [params.status] - 状态：draft/published
 * @param {string} [params.keyword] - 关键词
 * @returns {Promise} 分页报告列表
 */
export function getReportList(params) {
  return request({
    method: 'post',
    url: '/v1/reports/list',
    data: params
  })
}

/**
 * 获取报告详情
 * @param {number} id - 报告 ID
 * @returns {Promise} 报告详情
 */
export function getReportDetail(id) {
  return request({
    method: 'post',
    url: `/v1/reports/${id}`
  })
}

/**
 * 生成报告
 * @param {Object} data - 生成参数
 * @param {string} data.type - 报告类型：daily/quarterly/event
 * @param {number[]} [data.reservoir_ids] - 水库 ID 列表
 * @param {number} [data.alert_id] - 预警 ID（事件报告时传）
 * @returns {Promise} { report_id, status }
 */
export function generateReport(data) {
  return request({
    method: 'post',
    url: '/v1/reports/generate',
    data
  })
}

/**
 * 审核报告
 * @param {number} id - 报告 ID
 * @param {Object} data
 * @param {string} data.action - approve/reject
 * @param {string} [data.comment] - 审核备注
 * @returns {Promise}
 */
export function reviewReport(id, data) {
  return request({
    method: 'post',
    url: `/v1/reports/${id}/review`,
    data
  })
}

/**
 * 导出报告
 * @param {number} id - 报告 ID
 * @param {string} [format] - 导出格式：markdown
 * @returns {Promise} 报告文本内容
 */
export function exportReport(id, format = 'markdown') {
  return request({
    method: 'post',
    url: `/v1/reports/${id}/export`,
    data: { format }
  })
}
