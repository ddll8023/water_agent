import request from '@/utils/request'

/**
 * 创建指标
 * @param {Object} data - 创建指标请求参数
 * @returns {Promise} 创建结果
 */
export function createIndicator(data) {
  return request({
    method: 'post',
    url: '/indicators/create',
    data
  })
}

/**
 * 获取指标列表（分页）
 * @param {Object} data - 查询参数
 * @returns {Promise} 指标列表数据
 */
export function getIndicatorList(data) {
  return request({
    method: 'post',
    url: '/indicators/list',
    data
  })
}

/**
 * 获取指标详情
 * @param {number} id - 指标ID
 * @returns {Promise} 指标详情数据
 */
export function getIndicatorDetail(id) {
  return request({
    method: 'get',
    url: `/indicators/${id}`
  })
}

/**
 * 更新指标
 * @param {number} id - 指标ID
 * @param {Object} data - 更新指标请求参数
 * @returns {Promise} 更新结果
 */
export function updateIndicator(id, data) {
  return request({
    method: 'put',
    url: `/indicators/${id}`,
    data
  })
}

/**
 * 删除指标
 * @param {number} id - 指标ID
 * @returns {Promise} 删除结果
 */
export function deleteIndicator(id) {
  return request({
    method: 'delete',
    url: `/indicators/${id}`
  })
}