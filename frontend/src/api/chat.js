/**
 * 智能问答 API
 * SSE 流式对话 + 会话列表
 */

import request from '@/utils/request'

export function getChatList(params = {}) {
  return request.get('/v1/chat', { params })
}

export function fetchChatStream({ query, session_id, onChunk, onDone, onError }) {
  const controller = new AbortController()
  const token = localStorage.getItem('token')

  ;(async () => {
    try {
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ query, session_id }),
        signal: controller.signal,
      })

      if (!response.ok) {
        onError?.(new Error(`请求失败 (${response.status})`))
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          for (const line of part.split('\n')) {
            if (line.startsWith('data: ')) {
              try {
                const event = JSON.parse(line.slice(6))
                switch (event.type) {
                  case 'chunk':
                    onChunk?.(event.content)
                    break
                  case 'done':
                    onDone?.({ session_id: event.session_id, message_id: event.message_id })
                    break
                }
              } catch {
                /* 单条事件解析失败，静默跳过 */
              }
            }
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') return
      onError?.(err)
    }
  })()

  return controller
}
