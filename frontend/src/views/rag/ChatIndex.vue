<template>
  <el-container class="h-[calc(100vh-7rem)]">
    <!-- 左侧：对话历史侧边栏 -->
    <el-aside
      :width="sidebarCollapsed ? '0' : '260px'"
      class="bg-white border-r border-gray-200 flex flex-col transition-all duration-300 overflow-hidden"
    >
      <div v-if="!sidebarCollapsed" class="flex flex-col h-full">
        <div class="p-3 border-b border-gray-100">
          <el-button type="primary" class="w-full" @click="newSession">
            <el-icon><Plus /></el-icon>
            新对话
          </el-button>
        </div>

        <el-scrollbar class="flex-1" v-loading="sessionsLoading">
          <el-empty
            v-if="!sessionsLoading && sessions.length === 0"
            description="暂无对话记录，点击上方按钮开始提问"
            :image-size="80"
          />
          <div v-else class="flex flex-col">
            <div
              v-for="s in sessions" :key="s.id"
              class="group relative flex items-center justify-between w-full overflow-hidden cursor-pointer px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors"
              :class="{ 'bg-teal-50 !border-teal-100': currentSessionId === s.id }"
              @click="switchSession(s.id)"
            >
              <div class="flex flex-col gap-1 min-w-0 flex-1">
                <span class="text-sm truncate" :class="{ 'text-teal-700 font-medium': currentSessionId === s.id }">{{ s.title }}</span>
                <span class="text-xs text-gray-400">{{ formatTime(s.created_at) }}</span>
              </div>
              <el-button
                size="small"
                text
                type="danger"
                class="!opacity-0 group-hover:!opacity-100 transition-opacity shrink-0 ml-2"
                @click.stop="handleDelete(s.id, $event)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </el-scrollbar>
      </div>

      <!-- 折叠按钮 -->
      <button
        class="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-12 bg-white border border-gray-200 rounded-r-md flex items-center justify-center cursor-pointer text-gray-400 hover:text-gray-600 z-10"
        @click="sidebarCollapsed = !sidebarCollapsed"
      >
        <el-icon>
          <DArrowLeft v-if="!sidebarCollapsed" />
          <DArrowRight v-else />
        </el-icon>
      </button>
    </el-aside>

    <!-- 右侧：主对话区 -->
    <el-container class="flex-1 flex flex-col min-w-0">
      <!-- 顶部标题栏 -->
      <header class="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
        <div>
          <h2 class="text-base font-semibold text-gray-900">水质智能助手</h2>
          <p class="text-xs text-gray-400">基于标准规范和历史案例的知识问答</p>
        </div>
        <div v-if="sidebarCollapsed" class="flex items-center gap-2">
          <el-button text @click="sidebarCollapsed = false">
            <el-icon><DArrowRight /></el-icon>
            历史对话
          </el-button>
          <el-button type="primary" text @click="newSession">
            <el-icon><Plus /></el-icon>
            新对话
          </el-button>
        </div>
      </header>

      <!-- 消息列表 -->
      <el-scrollbar ref="scrollbarRef" class="flex-1 px-6 py-4" max-height="100%">
        <!-- 初始状态：推荐问题 -->
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
          <el-icon class="text-5xl text-gray-300 mb-4"><ChatLineSquare /></el-icon>
          <h3 class="text-base font-medium text-gray-700 mb-4">试试这样问</h3>
          <div class="flex flex-wrap justify-center gap-3 max-w-lg">
            <el-tag
              v-for="q in recommendedQuestions"
              :key="q"
              class="cursor-pointer hover:!bg-teal-50 !px-4 !py-2 !h-auto !text-sm !border-teal-200 !text-teal-700 !rounded-full transition-colors"
              @click="sendQuestion(q)"
            >
              {{ q }}
            </el-tag>
          </div>
        </div>

        <!-- 消息气泡 -->
        <div v-for="(msg, index) in messages" :key="msg.id || index" class="mb-6">
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" class="flex justify-end">
            <div class="max-w-[70%] bg-teal-500 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap">
              {{ msg.content }}
            </div>
          </div>

          <!-- AI 消息 -->
          <div v-else class="flex justify-start">
            <div class="max-w-[70%] bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm leading-relaxed shadow-sm">
              <!-- 正文 -->
              <div class="markdown-body" v-html="renderMarkdown(msg.content)" />

              <!-- 流式光标 -->
              <span
                v-if="msg.streaming"
                class="inline-block w-2 h-4 bg-teal-500 ml-0.5 animate-pulse"
              />

              <!-- 错误状态 -->
              <div
                v-if="msg.error"
                class="mt-2 p-2 bg-red-50 border border-red-200 rounded-lg"
              >
                <p class="text-xs text-red-600">{{ msg.error }}</p>
                <el-button
                  size="small"
                  type="danger"
                  text
                  class="mt-1 !text-xs"
                  @click="retry(msg)"
                >
                  <el-icon><Refresh /></el-icon>
                  重新生成
                </el-button>
              </div>

              <!-- 参考来源 -->
              <div v-if="!msg.streaming && msg.references && msg.references.length > 0" class="mt-3 border-t border-gray-100 pt-2">
                <el-collapse accordion>
                  <el-collapse-item title="参考来源" name="references">
                    <div v-for="(ref, i) in msg.references" :key="i" class="text-xs text-gray-500 py-1">
                      <el-icon class="mr-1"><Document /></el-icon>
                      文档 #{{ ref.doc_id }} · 第{{ ref.chunk_index }}段
                    </div>
                    <div v-if="msg.references.length === 0" class="text-xs text-gray-400 py-1">
                      暂无参考来源，回答基于通用知识生成
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>
          </div>
        </div>
      </el-scrollbar>

      <!-- 底部输入区 -->
      <footer class="shrink-0 bg-white border-t border-gray-200 px-6 py-4">
        <div class="flex gap-3">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="3"
            placeholder="输入水质相关问题..."
            resize="none"
            :disabled="isStreaming"
            @keydown="handleKeydown"
          />
          <div class="flex flex-col gap-2 shrink-0">
            <el-button
              type="primary"
              :disabled="!inputText.trim() || isStreaming"
              @click="sendMessage"
            >
              <el-icon><Promotion /></el-icon>
              发送
            </el-button>
            <el-button
              :disabled="messages.length === 0 || isStreaming"
              @click="clearMessages"
            >
              清空对话
            </el-button>
          </div>
        </div>
        <p class="text-xs text-gray-400 mt-2">Enter 发送 · Shift+Enter 换行</p>
      </footer>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { fetchChatStream, getChatList, getChatDetail, deleteChat } from '@/api/chat'
import {
  Plus, ChatLineSquare, Promotion, Refresh, Delete,
  DArrowLeft, DArrowRight, Document,
} from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'

/* ========== 状态 ========== */

const sidebarCollapsed = ref(false)
const scrollbarRef = ref(null)
const inputText = ref('')
const isStreaming = ref(false)
const sessionsLoading = ref(false)
const sessionLoading = ref(false)

// 会话列表（从 API 加载）
const sessions = ref([])
// 消息缓存：Map<sessionId, Message[]>
const messageCache = ref(new Map())
// 当前对话消息
const messages = ref([])
// 当前对话 ID
const currentSessionId = ref(null)
// SSE 控制器（用于取消）
let abortController = null

let msgIdCounter = Date.now()

const recommendedQuestions = [
  '氨氮超标Ⅲ类限值是多少？',
  '总磷超标怎么处理？',
  '蓝藻水华有什么前兆？',
  '暴雨后水质异常排查流程',
]

/* ========== 方法 ========== */

async function fetchSessions() {
  sessionsLoading.value = true
  try {
    const res = await getChatList({ page: 1, page_size: 50 })
    sessions.value = res.data.lists
  } catch {
    sessions.value = []
  } finally {
    sessionsLoading.value = false
  }
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

function genId() {
  return ++msgIdCounter
}

function newSession() {
  if (isStreaming.value) return
  // 保存当前会话消息
  if (currentSessionId.value) {
    messageCache.value.set(currentSessionId.value, [...messages.value])
  }
  currentSessionId.value = null
  messages.value = []
  inputText.value = ''
}

function switchSession(index) {
  if (isStreaming.value) return
  const id = Number(index)
  if (id === currentSessionId.value) return

  // 保存当前会话
  if (currentSessionId.value) {
    messageCache.value.set(currentSessionId.value, [...messages.value])
  }

  currentSessionId.value = id

  // 优先使用缓存
  const cached = messageCache.value.get(id)
  if (cached) {
    messages.value = cached
    return
  }

  // 缓存未命中则从 API 加载
  loadSessionMessages(id)
}

async function loadSessionMessages(id) {
  sessionLoading.value = true
  try {
    const res = await getChatDetail(id)
    const msgs = (res.data.messages || []).map(toMessage)
    messageCache.value.set(id, msgs)
    messages.value = msgs
  } catch (e) {
    messages.value = [
      { id: genId(), role: 'assistant', content: '', references: [], streaming: false, error: e.message || '加载对话失败' },
    ]
  } finally {
    sessionLoading.value = false
  }
}

function toMessage(item) {
  return {
    id: item.id,
    role: item.role,
    content: item.content,
    references: item.reference || [],
    streaming: false,
    error: null,
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return

  inputText.value = ''

  // 添加用户消息（先 push 再通过 index 取 reactive proxy）
  messages.value.push({ id: genId(), role: 'user', content: text })

  // 添加空的 AI 消息占位
  messages.value.push({
    id: genId(),
    role: 'assistant',
    content: '',
    references: [],
    streaming: true,
    error: null,
  })

  const aiMsg = messages.value[messages.value.length - 1]

  isStreaming.value = true
  scrollToBottom()

  abortController = fetchChatStream({
    query: text,
    session_id: currentSessionId.value,
    onChunk(content) {
      aiMsg.content += content
      scrollToBottom()
    },
    onDone(data) {
      aiMsg.streaming = false

      // 首次对话：记录 session
      if (!currentSessionId.value) {
        currentSessionId.value = data.session_id
        sessions.value.unshift({
          id: data.session_id,
          title: text.length > 20 ? text.slice(0, 20) + '...' : text,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        })
        messageCache.value.set(data.session_id, [...messages.value])
      } else {
        messageCache.value.set(currentSessionId.value, [...messages.value])
      }

      isStreaming.value = false
      scrollToBottom()
    },
    onError(err) {
      aiMsg.streaming = false
      aiMsg.error = err.message || '生成失败，请重试'
      isStreaming.value = false
      scrollToBottom()
    },
  })
}

function retry(msg) {
  // 找到对应的 user 消息
  const idx = messages.value.indexOf(msg)
  if (idx < 1) return
  const userMsg = messages.value[idx - 1]
  if (!userMsg || userMsg.role !== 'user') return

  msg.error = null
  msg.content = ''
  msg.streaming = true

  isStreaming.value = true

  abortController = fetchChatStream({
    query: userMsg.content,
    session_id: currentSessionId.value,
    onChunk(content) {
      msg.content += content
      scrollToBottom()
    },
    onDone(data) {
      msg.streaming = false
      isStreaming.value = false
      scrollToBottom()
    },
    onError(err) {
      msg.streaming = false
      msg.error = err.message || '生成失败，请重试'
      isStreaming.value = false
      scrollToBottom()
    },
  })
}

function clearMessages() {
  if (isStreaming.value) return
  messages.value = []
  if (currentSessionId.value) {
    messageCache.value.set(currentSessionId.value, [])
  }
}

async function handleDelete(sessionId, event) {
  event.stopPropagation()
  if (isStreaming.value) return

  try {
    await ElMessageBox.confirm('删除后将无法恢复，确认删除该对话？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteChat(sessionId)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    messageCache.value.delete(sessionId)
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null
      messages.value = []
    }
    ElMessage.success('对话已删除')
  } catch (e) {
    if (e === 'cancel') return
    ElMessage.error(e.message || '删除失败')
  }
}

function sendQuestion(q) {
  inputText.value = q
  sendMessage()
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function scrollToBottom() {
  nextTick(() => {
    const el = scrollbarRef.value?.wrapRef
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  })
}

onMounted(() => {
  fetchSessions()
})

watch(
  () => messages.value.length,
  () => scrollToBottom(),
)

/* ========== Markdown 轻量渲染 ========== */

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function renderMarkdown(text) {
  if (!text) return ''
  let html = escapeHtml(text)

  // 代码块（多行）
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre class="bg-gray-100 rounded-lg p-3 my-2 overflow-x-auto text-xs"><code>${escapeHtml(code)}</code></pre>`
  })

  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1.5 py-0.5 rounded text-xs text-red-500">$1</code>')

  // 加粗 **text**
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

  // 斜体 *text*
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')

  // 无序列表
  html = html.replace(/^- (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
  html = html.replace(/(<li.*<\/li>\n?)+/g, '<ul class="my-1">$&</ul>')

  // 有序列表
  html = html.replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal">$1</li>')
  html = html.replace(/(<li.*<\/li>\n?)+/g, (match) => {
    if (!match.startsWith('<ul')) return `<ol class="my-1">${match}</ol>`
    return match
  })

  // 换行
  html = html.replace(/\n/g, '<br>')

  return html
}
</script>

<style scoped>
.markdown-body {
  word-break: break-word;
}
.markdown-body :deep(pre) {
  white-space: pre-wrap;
}
.markdown-body :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
}
.markdown-body :deep(strong) {
  font-weight: 600;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 0;
}
</style>
