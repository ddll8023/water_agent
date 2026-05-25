import request from '@/utils/request'

export function getUserList(data) {
  return request({
    method: 'get',
    url: '/users/list',
    data
  })
}