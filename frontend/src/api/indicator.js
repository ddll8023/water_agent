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