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

export function getRoleDetail(id) {
  return request({
    method: 'get',
    url: `/roles/${id}`
  })
}

export function updateRole(data) {
  return request({
    method: 'put',
    url: '/roles/update',
    data
  })
}

export function deleteRole(id) {
  return request({
    method: 'delete',
    url: `/roles/${id}`
  })
}
