import request from '@/utils/request'

/**
 * 获取监测站点列表（分页）
 * @param {Object} params - 查询参数
 * @returns {Promise} 站点列表数据
 */
export function getStationList(params) {
  return request({
    method: 'get',
    url: '/stations/list',
    params
  })
}

/**
 * 创建监测站点
 * @param {Object} data - 创建站点请求参数
 * @returns {Promise} 创建结果
 */
export function createStation(data) {
  return request({
    method: 'post',
    url: '/stations/create',
    data
  })
}

/**
 * 获取监测站点详情
 * @param {number} id - 站点ID
 * @returns {Promise} 站点详情
 */
export function getStationDetail(id) {
  return request({
    method: 'get',
    url: `/stations/${id}`
  })
}

/**
 * 更新监测站点
 * @param {number} id - 站点ID
 * @param {Object} data - 更新站点请求参数
 * @returns {Promise} 更新结果
 */
export function updateStation(id, data) {
  return request({
    method: 'put',
    url: `/stations/${id}`,
    data
  })
}

/**
 * 删除监测站点
 * @param {number} id - 站点ID
 * @returns {Promise} 删除结果
 */
export function deleteStation(id) {
  return request({
    method: 'delete',
    url: `/stations/${id}`
  })
}
