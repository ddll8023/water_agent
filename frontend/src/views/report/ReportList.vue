<template>
  <div class="p-6">
    <header class="mb-6">
      <h1 class="text-xl font-semibold text-gray-900">报告中心</h1>
      <p class="text-sm text-gray-500 mt-1">查看和生成水质巡检、月度评估、季度评估与事件应急报告</p>
    </header>

    <section class="bg-white rounded-lg shadow-sm p-4 mb-4 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3 flex-wrap">
        <el-select v-model="filters.type" placeholder="报告类型" clearable class="w-32">
          <el-option label="全部" value="" />
          <el-option label="日巡检" value="daily" />
          <el-option label="月度评估" value="monthly" />
          <el-option label="季度评估" value="quarterly" />
          <el-option label="事件应急" value="event" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态" clearable class="w-28">
          <el-option label="全部" value="" />
          <el-option label="草稿" value="draft" />
          <el-option label="已发布" value="published" />
        </el-select>
        <el-input v-model="filters.keyword" placeholder="搜索报告标题" clearable class="w-56" @clear="handleSearch" @keyup.enter="handleSearch">
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
      <el-button v-if="authStore.isAdmin" type="primary" @click="generateDialogVisible = true">
        <el-icon><Plus /></el-icon>
        生成报告
      </el-button>
    </section>

    <section v-loading="loading" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <el-card v-for="item in reportList" :key="item.id" shadow="sm" class="cursor-pointer hover:shadow-md transition-shadow" @click="handleViewDetail(item.id)">
        <div class="flex items-start justify-between mb-3">
          <el-tag :type="getTypeTag(item.report_type)" size="small">{{ getTypeLabel(item.report_type) }}</el-tag>
          <el-tag v-if="item.status === 'published'" type="success" size="small">已发布</el-tag>
          <el-tag v-else type="info" size="small">草稿</el-tag>
        </div>
        <h3 class="text-base font-medium text-gray-800 mb-2 truncate">{{ item.title }}</h3>
        <div class="text-sm text-gray-500 space-y-1">
          <div>创建时间：{{ formatDateTime(item.created_at) }}</div>
          <div v-if="item.published_at">发布时间：{{ formatDateTime(item.published_at) }}</div>
        </div>
      </el-card>
      <el-empty v-if="!loading && !reportList.length" description="暂无报告" class="col-span-full" />
    </section>

    <div v-if="pagination.total > pagination.pageSize" class="flex justify-end mt-4">
      <el-pagination
        :current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next"
        @update:current-page="handlePageChange"
      />
    </div>

    <el-dialog v-model="generateDialogVisible" title="生成报告" width="550px" :close-on-click-modal="false">
      <el-form :model="generateForm" label-width="100px">
        <el-form-item label="报告类型">
          <el-select v-model="generateForm.type" placeholder="请选择报告类型" class="w-full">
            <el-option label="日巡检报告" value="daily" />
            <el-option label="月度水质报告" value="monthly" />
            <el-option label="季度水质报告" value="quarterly" />
            <el-option label="事件应急报告" value="event" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="generateForm.startDate" type="date" placeholder="选择开始日期" class="w-full" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="generateForm.endDate" type="date" placeholder="选择结束日期" class="w-full" value-format="YYYY-MM-DD" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="generateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="handleGenerate">开始生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/format'
import { getReportList, generateReport } from '@/api/report'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const reportList = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 12,
  total: 0
})
const filters = reactive({
  type: '',
  status: '',
  keyword: ''
})

const generateDialogVisible = ref(false)
const generating = ref(false)
const generateForm = reactive({
  type: '',
  startDate: '',
  endDate: ''
})

function getTypeLabel(type) {
  const map = { daily: '日巡检', monthly: '月度评估', quarterly: '季度评估', event: '事件应急' }
  return map[type] || type
}

function getTypeTag(type) {
  const map = { daily: '', monthly: 'success', quarterly: 'primary', event: 'warning' }
  return map[type] || 'info'
}

function handleSearch() {
  pagination.page = 1
  fetchReportList()
}

function handlePageChange(page) {
  pagination.page = page
  fetchReportList()
}

function handleViewDetail(id) {
  router.push(`/reports/${id}`)
}

async function fetchReportList() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filters.type) params.report_type = filters.type
    if (filters.status) params.status = filters.status
    if (filters.keyword) params.keyword = filters.keyword

    const res = await getReportList(params)
    reportList.value = res.data.lists || []
    pagination.total = res.data.pagination?.total || 0
  } catch (e) {
    ElMessage.error(e.message || '加载报告列表失败')
  } finally {
    loading.value = false
  }
}

async function handleGenerate() {
  if (!generateForm.type) {
    ElMessage.warning('请选择报告类型')
    return
  }
  if (!generateForm.startDate || !generateForm.endDate) {
    ElMessage.warning('请选择日期范围')
    return
  }
  generating.value = true
  try {
    await generateReport({
      report_type: generateForm.type,
      start_date: generateForm.startDate,
      end_date: generateForm.endDate
    })
    generateDialogVisible.value = false
    ElMessage.success('报告生成任务已提交，请稍后查看')
    setTimeout(fetchReportList, 2000)
  } catch (e) {
    ElMessage.error(e.message || '提交生成任务失败')
  } finally {
    generating.value = false
  }
}

onMounted(() => {
  fetchReportList()
})
</script>
