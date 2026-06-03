import request from '@/utils/request'

/**
 * 获取预警列表（分页）
 * @param {Object} params - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页记录数
 * @param {number} [params.reservoir_id] - 水库 ID
 * @param {string} [params.alert_level] - 预警等级：info/warning/critical
 * @param {number} [params.status] - 状态：0=待确认/1=已确认/2=处置中/3=已解决
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

/**
 * 获取预警详情
 * @param {number} id - 预警 ID
 * @returns {Promise} 预警详情数据
 */
export function getAlertDetail(id) {
  return request({
    method: 'get',
    url: `/v1/alerts/${id}`
  })
}

/**
 * 更新预警状态
 * @param {number} id - 预警 ID
 * @param {Object} data - 更新数据
 * @param {number} data.status - 目标状态：1=已确认 / 2=处置中 / 3=已解决
 * @param {number} [data.handler_id] - 处理人 ID
 * @returns {Promise}
 */
export function updateAlert(id, data) {
  return request({
    method: 'put',
    url: `/v1/alerts/${id}`,
    data
  })
}

/**
 * 提交处置备注
 * @param {number} id - 预警 ID
 * @param {string} content - 备注内容
 * @returns {Promise}
 */
export function submitAlertNote(id, content) {
  return request({
    method: 'post',
    url: `/v1/alerts/${id}/notes`,
    data: { content }
  })
}
