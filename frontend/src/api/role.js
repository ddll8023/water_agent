import request from '@/utils/request'

export function getRoleList(params) {
  return request({
    method: 'get',
    url: '/roles/list',
    params
  })
}

export function addRole(data) {
  return request({
    method: 'post',
    url: '/roles/add',
    data
  })
}
