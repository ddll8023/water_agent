import request from '@/utils/request'

/**
 * 提交 Agent 任务
 * @param {Object} data
 * @param {string} data.agent_type - emergency/report
 * @param {Object} data.params - 任务参数
 * @returns {Promise} { task_id, status }
 */
export function submitAgentTask(data) {
  return request({
    method: 'post',
    url: '/v1/agent/task',
    data
  })
}

/**
 * 查询任务状态
 * @param {string} taskId - 任务 ID
 * @returns {Promise} { status, progress, result, error }
 */
export function getAgentTaskStatus(taskId) {
  return request({
    method: 'get',
    url: `/v1/agent/task/${taskId}`
  })
}

/**
 * 恢复任务（审批）
 * @param {string} taskId - 任务 ID
 * @param {Object} data
 * @param {string} data.action - approve/reject
 * @param {string} [data.comment] - 备注
 * @returns {Promise}
 */
export function resumeAgentTask(taskId, data) {
  return request({
    method: 'post',
    url: `/v1/agent/task/${taskId}/resume`,
    data
  })
}

/**
 * 取消任务
 * @param {string} taskId - 任务 ID
 * @returns {Promise}
 */
export function cancelAgentTask(taskId) {
  return request({
    method: 'delete',
    url: `/v1/agent/task/${taskId}`
  })
}

/**
 * 获取巡检日志列表
 * @param {Object} params
 * @param {number} [params.status] - 执行状态筛选
 * @param {string} [params.start_time] - 开始时间
 * @param {string} [params.end_time] - 结束时间
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页记录数
 * @returns {Promise} 分页日志列表
 */
export function getPatrolLogList(params) {
  return request({
    method: 'post',
    url: '/v1/patrol-logs/list',
    data: params
  })
}

/**
 * 删除巡检日志
 * @param {number} id - 日志 ID
 * @returns {Promise}
 */
export function deletePatrolLog(id) {
  return request({
    method: 'delete',
    url: `/v1/patrol-logs/${id}`
  })
}
