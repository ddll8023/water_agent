import request from '@/utils/request'

/**
 * 获取预警规则列表（分页）
 * @param {Object} data - 查询参数
 * @param {number} [data.indicator_id] - 指标ID筛选
 * @param {number} [data.reservoir_id] - 水库ID筛选
 * @param {number} [data.is_active] - 启用状态筛选
 * @param {number} data.page - 页码
 * @param {number} data.page_size - 每页记录数
 * @returns {Promise} 规则分页数据
 */
export function getAlertRuleList(data) {
  return request({
    method: 'post',
    url: '/v1/alert-rules/list',
    data
  })
}

/**
 * 获取预警规则详情
 * @param {number} id - 规则ID
 * @returns {Promise} 规则详情
 */
export function getAlertRuleDetail(id) {
  return request({
    method: 'get',
    url: `/v1/alert-rules/${id}`
  })
}

/**
 * 创建预警规则
 * @param {Object} data - 创建参数
 * @returns {Promise}
 */
export function createAlertRule(data) {
  return request({
    method: 'post',
    url: '/v1/alert-rules/create',
    data
  })
}

/**
 * 更新预警规则
 * @param {number} id - 规则ID
 * @param {Object} data - 更新参数
 * @returns {Promise}
 */
export function updateAlertRule(id, data) {
  return request({
    method: 'put',
    url: `/v1/alert-rules/${id}`,
    data
  })
}

/**
 * 删除预警规则
 * @param {number} id - 规则ID
 * @returns {Promise}
 */
export function deleteAlertRule(id) {
  return request({
    method: 'delete',
    url: `/v1/alert-rules/${id}`
  })
}
