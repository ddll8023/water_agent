import request from '@/utils/request'

export function getUserList(data) {
  return request({
    method: 'get',
    url: '/users/list',
    data
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