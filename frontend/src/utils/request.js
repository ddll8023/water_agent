import axios from 'axios'

const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => {
    const { data } = response
    if (data.code === 0) {
      return data
    }
    return Promise.reject(new Error(data.message || '请求失败'))
  },
  (error) => {
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      return Promise.reject(new Error('网络连接超时，请检查网络'))
    }
    if (error.response) {
      const { status, data } = error.response
      if (status === 401 || status === 403) {
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
        window.location.href = '/login'
        return Promise.reject(new Error('请先登录'))
      }
      const message = data?.message || `请求失败 (${status})`
      return Promise.reject(new Error(message))
    }
    if (error.request) {
      return Promise.reject(new Error('网络连接失败，请检查网络设置'))
    }
    return Promise.reject(error)
  }
)

export default request