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