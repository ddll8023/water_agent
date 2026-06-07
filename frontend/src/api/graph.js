import request from '@/utils/request'

/**
 * 获取图谱全局概览
 * @param {string} reservoirCode - 可选，水库编号
 * @returns {Promise}
 */
export function getGraphOverview(reservoirCode) {
  return request.get('/v1/graph/overview', {
    params: reservoirCode ? { reservoir_code: reservoirCode } : {}
  })
}

/**
 * 搜索图谱节点
 * @param {string} keyword - 搜索关键词
 * @param {string} type - 可选，节点类型
 * @returns {Promise}
 */
export function searchNodes(keyword, type) {
  return request.get('/v1/graph/search', {
    params: { keyword, type }
  })
}

/**
 * 获取节点详情
 * @param {string} type - 节点类型
 * @param {string} id - 节点标识
 * @returns {Promise}
 */
export function getNodeDetail(type, id) {
  return request.get(`/v1/graph/node/${type}/${id}`)
}

/**
 * 节点一跳扩展
 * @param {string} type - 节点类型
 * @param {string} id - 节点标识
 * @param {number} depth - 扩展深度
 * @returns {Promise}
 */
export function expandNode(type, id, depth = 1) {
  return request.get(`/v1/graph/expand/${type}/${id}`, {
    params: { depth }
  })
}

/**
 * 污染溯源路径
 * @param {string} reservoirCode - 水库编号
 * @param {string} indicatorCode - 可选，指标编号
 * @returns {Promise}
 */
export function tracePollution(reservoirCode, indicatorCode) {
  return request.get('/v1/graph/trace', {
    params: { reservoir_code: reservoirCode, indicator_code: indicatorCode }
  })
}
