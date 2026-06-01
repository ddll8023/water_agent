<template>
  <div>
    <el-breadcrumb separator="/" class="mb-4">
      <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>实时监测</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="never" class="mb-4">
      <div class="flex items-center justify-between">
        <div class="flex-1 min-w-0">
          <div class="flex items-baseline gap-3 mb-2">
            <h2 class="text-2xl font-semibold text-gray-900 leading-tight">
              <el-skeleton :loading="true" animated style="width: 180px">
                <template #template>
                  <el-skeleton-item variant="h1" style="width: 100%; height: 28px" />
                </template>
              </el-skeleton>
            </h2>
          </div>
          <div class="flex items-center gap-6 text-sm text-gray-500">
            <span class="flex items-center gap-1">
              <el-icon><Location /></el-icon>
              <el-skeleton :loading="true" animated style="width: 140px">
                <template #template>
                  <el-skeleton-item variant="text" style="width: 100%; height: 14px" />
                </template>
              </el-skeleton>
            </span>
            <span class="flex items-center gap-1">
              <el-icon><DataLine /></el-icon>
              <el-skeleton :loading="true" animated style="width: 120px">
                <template #template>
                  <el-skeleton-item variant="text" style="width: 100%; height: 14px" />
                </template>
              </el-skeleton>
            </span>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-500">水质类别</span>
          <el-skeleton :loading="true" animated style="width: 80px">
            <template #template>
              <el-skeleton-item variant="text" style="width: 100%; height: 32px; border-radius: 16px" />
            </template>
          </el-skeleton>
        </div>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="实时数据" name="realtime">
          <realtime-tab />
        </el-tab-pane>
        <el-tab-pane label="历史趋势" name="trend">
          <trend-tab />
        </el-tab-pane>
        <el-tab-pane label="监测站点" name="stations">
          <stations-tab />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <div class="fixed bottom-6 right-8 flex items-center gap-3 z-10">
      <el-button :icon="Document" @click="handleViewReports">
        查看巡检报告
      </el-button>
      <el-button type="primary" :icon="ChatLineRound" @click="aiDrawerVisible = true">
        智能问答
      </el-button>
    </div>

    <ai-chat-drawer v-model="aiDrawerVisible" :reservoir-name="''" />
  </div>
</template>

<script setup>
/**
 * 水库实时监测详情页
 * 功能描述：面包屑 + 水库信息栏 + 三 Tab 切换 + 底部固定操作区 + AI 问答抽屉
 * 依赖组件：RealtimeTab, TrendTab, StationsTab, AiChatDrawer
 */
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Location, DataLine, Document, ChatLineRound } from '@element-plus/icons-vue'
import RealtimeTab from './components/RealtimeTab.vue'
import TrendTab from './components/TrendTab.vue'
import StationsTab from './components/StationsTab.vue'
import AiChatDrawer from './components/AiChatDrawer.vue'

const route = useRoute()
const activeTab = ref('realtime')
const aiDrawerVisible = ref(false)

const handleViewReports = () => {
  ElMessage.info('巡检报告功能开发中')
}
</script>
