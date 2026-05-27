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
