/**
 * WebSocket 实时预警推送
 * 功能描述：连接 WebSocket 接收新预警通知，断线自动重连
 * 依赖组件：ElNotification
 */
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElNotification } from 'element-plus'

const WS_URL = `ws://${location.hostname}:3443/ws/alerts`
const RECONNECT_INTERVAL = 5000

export function useAlertWebSocket() {
  let ws = null
  let reconnectTimer = null
  const router = useRouter()

  const scheduleReconnect = () => {
    if (reconnectTimer) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, RECONNECT_INTERVAL)
  }

  const connect = () => {
    try {
      ws = new WebSocket(WS_URL)
    } catch {
      scheduleReconnect()
      return
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'new_alert' && msg.data) {
          ElNotification({
            title: '新预警通知',
            message: msg.data.title || '收到新预警',
            type: 'warning',
            duration: 8000,
            onClick: () => router.push(`/alerts/${msg.data.id}`)
          })
        }
      } catch {
        /* 消息解析失败，静默忽略 */
      }
    }

    ws.onclose = () => {
      ws = null
      scheduleReconnect()
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
  }

  onMounted(connect)
  onUnmounted(disconnect)
}
