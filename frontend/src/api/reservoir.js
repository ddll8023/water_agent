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
