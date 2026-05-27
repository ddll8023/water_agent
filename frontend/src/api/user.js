import request from '@/utils/request'

export function getUserList(params) {
  return request({
    method: 'get',
    url: '/users/list',
    params
  })
}

export function addUser(data) {
  return request({
    method: 'post',
    url: '/users/add',
    data
  })
}

export function getUserDetail(id) {
  return request({
    method: 'get',
    url: `/users/${id}`
  })
}

export function updateUser(id, data) {
  return request({
    method: 'put',
    url: `/users/${id}`,
    data
  })
}

export function resetPassword(id, data) {
  return request({
    method: 'post',
    url: `/users/${id}/reset-password`,
    data
  })
}