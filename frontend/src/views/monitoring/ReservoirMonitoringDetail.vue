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
              {{ reservoirName || '加载中...' }}
            </h2>
            <el-tag v-if="reservoirCode" type="info" size="small">{{ reservoirCode }}</el-tag>
          </div>
          <div class="flex items-center gap-6 text-sm text-gray-500">
            <span v-if="reservoirLocation" class="flex items-center gap-1">
              <el-icon><Location /></el-icon>
              {{ reservoirLocation }}
            </span>
            <span v-if="reservoirWatershed" class="flex items-center gap-1">
              <el-icon><DataLine /></el-icon>
              {{ reservoirWatershed }}
            </span>
          </div>
        </div>

        <div v-if="waterGrade" class="flex items-center gap-2">
          <span class="text-sm text-gray-500">水质类别</span>
          <el-tag :type="gradeTagType" size="large" effect="dark">{{ waterGrade }}</el-tag>
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

    <ai-chat-drawer v-model="aiDrawerVisible" :reservoir-name="reservoirName" />
  </div>
</template>

<script setup>
/**
 * 水库实时监测详情页
 * 功能描述：面包屑 + 水库信息栏（对接真实数据）+ 三 Tab 切换 + 底部固定操作区 + AI 问答抽屉
 * 依赖组件：RealtimeTab, TrendTab, StationsTab, AiChatDrawer
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Location, DataLine, Document, ChatLineRound } from '@element-plus/icons-vue'
import { getReservoirDetail } from '@/api/reservoir'
import RealtimeTab from './components/RealtimeTab.vue'
import TrendTab from './components/TrendTab.vue'
import StationsTab from './components/StationsTab.vue'
import AiChatDrawer from './components/AiChatDrawer.vue'

const route = useRoute()
const activeTab = ref('realtime')
const aiDrawerVisible = ref(false)

const reservoirName = ref('')
const reservoirCode = ref('')
const reservoirLocation = ref('')
const reservoirWatershed = ref('')
const waterGrade = ref('')

const gradeTagType = computed(() => {
  const map = { 'Ⅰ类': 'success', 'Ⅱ类': 'success', 'Ⅲ类': 'warning', 'Ⅳ类': 'danger', 'Ⅴ类': 'danger' }
  return map[waterGrade.value] || 'info'
})

const handleViewReports = () => {
  ElMessage.info('巡检报告功能开发中')
}

onMounted(async () => {
  const id = Number(route.params.id)
  if (!id) return
  try {
    const res = await getReservoirDetail(id)
    const data = res.data
    if (data) {
      reservoirName.value = data.name || ''
      reservoirCode.value = data.code || ''
      reservoirLocation.value = data.location || ''
      reservoirWatershed.value = data.watershed || ''
      waterGrade.value = data.water_grade || ''
    }
  } catch {
    ElMessage.error('获取水库详情失败')
  }
})
</script>
