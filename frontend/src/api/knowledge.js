import request from '@/utils/request'

/**
 * 上传知识库文档
 * @param {FormData} formData - 包含 files[] 和 category 的 FormData
 * @returns {Promise} 批量上传结果
 */
export function uploadDocuments(formData) {
  return request({
    method: 'post',
    url: '/v1/documents/upload',
    headers: { 'Content-Type': 'multipart/form-data' },
    data: formData
  })
}

/**
 * 获取知识库文档列表（分页）
 * @param {Object} params - 查询参数
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页记录数
 * @param {string} [params.keyword] - 文件名关键字
 * @param {number} [params.doc_type] - 文档类型
 * @param {number} [params.status] - 处理状态
 * @returns {Promise} 分页文档列表
 */
export function getDocumentList(params) {
  return request({
    method: 'get',
    url: '/v1/documents',
    params
  })
}
