import request from '@/utils/request'

/**
 * 上传知识库文档
 * @param {FormData} formData - 包含 files[] 和 doc_type 的 FormData
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
