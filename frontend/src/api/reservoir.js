import request from '@/utils/request'

/**
 * 获取水库列表（分页）
 * @param {Object} data - 查询参数
 * @returns {Promise} 水库列表数据
 */
export function getReservoirList(params) {
  return request({
    method: 'get',
    url: '/reservoir/list',
    params
  })
}

/**
 * 创建水库
 * @param {Object} data - 创建水库请求参数
 * @returns {Promise} 创建结果
 */
export function createReservoir(data) {
  return request({
    method: 'post',
    url: '/reservoir/create',
    data
  })
}

/**
 * 获取水库详情
 * @param {number} id - 水库ID
 * @returns {Promise} 水库详情数据
 */
export function getReservoirDetail(id) {
  return request({
    method: 'get',
    url: `/reservoir/${id}`
  })
}

/**
 * 更新水库
 * @param {number} id - 水库ID
 * @param {Object} data - 更新水库请求参数
 * @returns {Promise} 更新结果
 */
export function updateReservoir(id, data) {
  return request({
    method: 'put',
    url: `/reservoir/${id}`,
    data
  })
}
