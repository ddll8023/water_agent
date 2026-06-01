<template>
  <el-drawer
    :model-value="modelValue"
    direction="rtl"
    size="500px"
    :with-header="false"
    @update:model-value="(v) => emit('update:modelValue', v)"
  >
    <div class="flex flex-col h-full">
      <header class="px-5 py-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold text-gray-900">水质智能助手</h2>
          <el-text type="info" size="small">基于标准规范和历史案例的知识问答</el-text>
        </div>
        <el-button text @click="close">
          <el-icon :size="18"><Close /></el-icon>
        </el-button>
      </header>

      <div class="flex-1 overflow-auto px-5 py-6 bg-gray-50">
        <el-empty description="AI 问答功能开发中" />
        <p class="text-center text-sm text-gray-500 mt-2">
          将基于 RAG 检索水质标准、异常处置流程、历史案例等专业问题
        </p>
      </div>

      <footer class="border-t border-gray-200 p-4 bg-white">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          :placeholder="placeholder"
          resize="none"
          disabled
        />
        <div class="flex justify-end gap-2 mt-2">
          <el-button :disabled="!inputText.trim()">发送</el-button>
        </div>
      </footer>
    </div>
  </el-drawer>
</template>

<script setup>
/**
 * AI 智能问答抽屉（占位）
 * 功能描述：UI 骨架与 el-drawer 容器，无真实对话逻辑
 * 依赖组件：无
 */
import { computed, ref } from 'vue'
import { Close } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  reservoirName: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue'])

const inputText = ref('')

const placeholder = computed(() =>
  props.reservoirName
    ? `请帮我分析${props.reservoirName}近期的水质变化趋势`
    : '请输入水质相关问题...'
)

const close = () => emit('update:modelValue', false)
</script>
