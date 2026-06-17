<template>
  <div>
    <el-breadcrumb separator="/" class="mb-4">
      <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item :to="{ path: '/reports/list' }">报告中心</el-breadcrumb-item>
      <el-breadcrumb-item>报告详情</el-breadcrumb-item>
    </el-breadcrumb>

    <div v-loading="loading">
      <el-card v-if="report" shadow="never" class="mb-4">
        <div class="flex items-center justify-between mb-4">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <h2 class="text-xl font-semibold text-gray-900">{{ report.title }}</h2>
              <el-tag :type="getTypeTag(report.report_type)" size="small">{{ getTypeLabel(report.report_type) }}</el-tag>
              <el-tag v-if="report.status === 'published'" type="success" size="small">已发布</el-tag>
              <el-tag v-else type="info" size="small">草稿</el-tag>
            </div>
            <div class="text-sm text-gray-500">
              <span>创建时间：{{ formatDateTime(report.created_at) }}</span>
              <span v-if="report.published_at" class="ml-4">发布时间：{{ formatDateTime(report.published_at) }}</span>
            </div>
          </div>
          <div v-if="report.status === 'draft'" class="flex gap-2">
            <el-button type="success" :loading="reviewLoading" @click="handleReview('approve')">审核发布</el-button>
            <el-button :loading="reviewLoading" @click="handleReview('reject')">驳回</el-button>
          </div>
        </div>

        <el-divider />

        <div v-if="report.sections" class="space-y-6">
          <div v-for="(sec, idx) in report.sections" :key="idx">
            <h3 class="text-lg font-semibold text-gray-800 mb-2">{{ sec.title }}</h3>
            <div class="text-gray-700 leading-relaxed whitespace-pre-wrap">{{ sec.content }}</div>
            <el-divider v-if="idx < report.sections.length - 1" />
          </div>
        </div>
        <div v-else class="text-gray-500">暂无报告内容</div>
      </el-card>

      <el-empty v-else-if="!loading" description="报告不存在" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTime } from '@/utils/format'
import { getReportDetail, reviewReport } from '@/api/report'

const route = useRoute()

const loading = ref(true)
const report = ref(null)
const reviewLoading = ref(false)

function getTypeLabel(type) {
  const map = { daily: '日巡检', monthly: '月度评估', quarterly: '季度评估', event: '事件应急' }
  return map[type] || type
}

function getTypeTag(type) {
  const map = { daily: '', monthly: 'success', quarterly: 'primary', event: 'warning' }
  return map[type] || 'info'
}

async function loadReportDetail() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const res = await getReportDetail(id)
    report.value = res.data
  } catch (e) {
    ElMessage.error(e.message || '加载报告详情失败')
  } finally {
    loading.value = false
  }
}

async function handleReview(action) {
  const text = action === 'approve' ? '确认发布该报告？' : '确认驳回该报告？'
  try {
    await ElMessageBox.confirm(text, '审核确认', { type: 'warning' })
    reviewLoading.value = true
    await reviewReport(route.params.id, { action })
    ElMessage.success(action === 'approve' ? '报告已发布' : '报告已驳回')
    loadReportDetail()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '操作失败')
    }
  } finally {
    reviewLoading.value = false
  }
}

onMounted(() => {
  loadReportDetail()
})
</script>
