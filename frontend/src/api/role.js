import request from '@/utils/request'

export function getRoleList(params) {
  return request({
    method: 'get',
    url: '/roles/list',
    params
  })
}
