import request from '@/utils/request'

/**
 * 获取河流列表（分页）
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getRiverList(params) {
  return request({
    method: 'get',
    url: '/v1/graph/admin/rivers/list',
    params
  })
}

/**
 * 创建河流
 * @param {Object} data - 创建河流参数
 * @returns {Promise}
 */
export function createRiver(data) {
  return request({
    method: 'post',
    url: '/v1/graph/admin/rivers/create',
    data
  })
}

/**
 * 获取河流详情
 * @param {string} name - 河流名称
 * @returns {Promise}
 */
export function getRiverDetail(name) {
  return request({
    method: 'get',
    url: `/v1/graph/admin/rivers/${encodeURIComponent(name)}`
  })
}

/**
 * 更新河流
 * @param {string} name - 河流名称
 * @param {Object} data - 更新参数
 * @returns {Promise}
 */
export function updateRiver(name, data) {
  return request({
    method: 'put',
    url: `/v1/graph/admin/rivers/${encodeURIComponent(name)}`,
    data
  })
}

/**
 * 删除河流
 * @param {string} name - 河流名称
 * @returns {Promise}
 */
export function deleteRiver(name) {
  return request({
    method: 'delete',
    url: `/v1/graph/admin/rivers/${encodeURIComponent(name)}`
  })
}

/**
 * 获取污染源列表（分页）
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getPollutionSourceList(params) {
  return request({
    method: 'get',
    url: '/v1/graph/admin/pollution-sources/list',
    params
  })
}

/**
 * 创建污染源
 * @param {Object} data - 创建污染源参数
 * @returns {Promise}
 */
export function createPollutionSource(data) {
  return request({
    method: 'post',
    url: '/v1/graph/admin/pollution-sources/create',
    data
  })
}

/**
 * 获取污染源详情
 * @param {string} name - 污染源名称
 * @returns {Promise}
 */
export function getPollutionSourceDetail(name) {
  return request({
    method: 'get',
    url: `/v1/graph/admin/pollution-sources/${encodeURIComponent(name)}`
  })
}

/**
 * 更新污染源
 * @param {string} name - 污染源名称
 * @param {Object} data - 更新参数
 * @returns {Promise}
 */
export function updatePollutionSource(name, data) {
  return request({
    method: 'put',
    url: `/v1/graph/admin/pollution-sources/${encodeURIComponent(name)}`,
    data
  })
}

/**
 * 删除污染源
 * @param {string} name - 污染源名称
 * @returns {Promise}
 */
export function deletePollutionSource(name) {
  return request({
    method: 'delete',
    url: `/v1/graph/admin/pollution-sources/${encodeURIComponent(name)}`
  })
}

/**
 * 获取水库列表（Neo4j直写，分页）
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getNeo4jReservoirList(params) {
  return request({
    method: 'get',
    url: '/v1/graph/admin/reservoirs/list',
    params
  })
}

/**
 * 创建水库（Neo4j直写）
 * @param {Object} data - 创建参数
 * @returns {Promise}
 */
export function createNeo4jReservoir(data) {
  return request({
    method: 'post',
    url: '/v1/graph/admin/reservoirs/create',
    data
  })
}

/**
 * 获取水库详情（Neo4j直写）
 * @param {string} code - 水库编号
 * @returns {Promise}
 */
export function getNeo4jReservoirDetail(code) {
  return request({
    method: 'get',
    url: `/v1/graph/admin/reservoirs/${encodeURIComponent(code)}`
  })
}

/**
 * 更新水库（Neo4j直写）
 * @param {string} code - 水库编号
 * @param {Object} data - 更新参数
 * @returns {Promise}
 */
export function updateNeo4jReservoir(code, data) {
  return request({
    method: 'put',
    url: `/v1/graph/admin/reservoirs/${encodeURIComponent(code)}`,
    data
  })
}

/**
 * 删除水库（Neo4j直写）
 * @param {string} code - 水库编号
 * @returns {Promise}
 */
export function deleteNeo4jReservoir(code) {
  return request({
    method: 'delete',
    url: `/v1/graph/admin/reservoirs/${encodeURIComponent(code)}`
  })
}

/**
 * 获取监测站点列表（Neo4j直写，分页）
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getNeo4jStationList(params) {
  return request({
    method: 'get',
    url: '/v1/graph/admin/stations/list',
    params
  })
}

/**
 * 创建监测站点（Neo4j直写）
 * @param {Object} data - 创建参数
 * @returns {Promise}
 */
export function createNeo4jStation(data) {
  return request({
    method: 'post',
    url: '/v1/graph/admin/stations/create',
    data
  })
}

/**
 * 获取监测站点详情（Neo4j直写）
 * @param {string} code - 站点编号
 * @returns {Promise}
 */
export function getNeo4jStationDetail(code) {
  return request({
    method: 'get',
    url: `/v1/graph/admin/stations/${encodeURIComponent(code)}`
  })
}

/**
 * 更新监测站点（Neo4j直写）
 * @param {string} code - 站点编号
 * @param {Object} data - 更新参数
 * @returns {Promise}
 */
export function updateNeo4jStation(code, data) {
  return request({
    method: 'put',
    url: `/v1/graph/admin/stations/${encodeURIComponent(code)}`,
    data
  })
}

/**
 * 删除监测站点（Neo4j直写）
 * @param {string} code - 站点编号
 * @returns {Promise}
 */
export function deleteNeo4jStation(code) {
  return request({
    method: 'delete',
    url: `/v1/graph/admin/stations/${encodeURIComponent(code)}`
  })
}

/**
 * 获取监测指标列表（Neo4j直写，分页）
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getNeo4jIndicatorList(params) {
  return request({
    method: 'get',
    url: '/v1/graph/admin/indicators/list',
    params
  })
}

/**
 * 创建监测指标（Neo4j直写）
 * @param {Object} data - 创建参数
 * @returns {Promise}
 */
export function createNeo4jIndicator(data) {
  return request({
    method: 'post',
    url: '/v1/graph/admin/indicators/create',
    data
  })
}

/**
 * 获取监测指标详情（Neo4j直写）
 * @param {string} code - 指标编码
 * @returns {Promise}
 */
export function getNeo4jIndicatorDetail(code) {
  return request({
    method: 'get',
    url: `/v1/graph/admin/indicators/${encodeURIComponent(code)}`
  })
}

/**
 * 更新监测指标（Neo4j直写）
 * @param {string} code - 指标编码
 * @param {Object} data - 更新参数
 * @returns {Promise}
 */
export function updateNeo4jIndicator(code, data) {
  return request({
    method: 'put',
    url: `/v1/graph/admin/indicators/${encodeURIComponent(code)}`,
    data
  })
}

/**
 * 删除监测指标（Neo4j直写）
 * @param {string} code - 指标编码
 * @returns {Promise}
 */
export function deleteNeo4jIndicator(code) {
  return request({
    method: 'delete',
    url: `/v1/graph/admin/indicators/${encodeURIComponent(code)}`
  })
}
