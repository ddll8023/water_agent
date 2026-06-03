<template>
  <div>
    <el-breadcrumb separator="/" class="mb-4">
      <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>预警中心</el-breadcrumb-item>
    </el-breadcrumb>

    <header class="flex items-center gap-2 mb-4">
      <h1 class="text-xl font-semibold text-gray-900">预警中心</h1>
      <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="!relative !top-0">
        <span />
      </el-badge>
    </header>

    <el-card shadow="never" class="mb-4">
      <el-form :model="filter" inline label-width="auto" @keyup.enter="handleSearch">
        <el-form-item label="所属水库">
          <el-select
            v-model="filter.reservoir_id"
            placeholder="全部"
            clearable
            filterable
            class="!w-44"
            @change="handleSearch"
          >
            <el-option
              v-for="item in reservoirOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="告警级别">
          <el-select
            v-model="filter.alert_level"
            placeholder="全部"
            clearable
            class="!w-36"
            @change="handleSearch"
          >
            <el-option label="提示" :value="1" />
            <el-option label="警告" :value="2" />
            <el-option label="严重" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理状态">
          <el-select
            v-model="filter.status"
            placeholder="全部"
            clearable
            class="!w-36"
            @change="handleSearch"
          >
            <el-option label="新增" :value="0" />
            <el-option label="已确认" :value="1" />
            <el-option label="处理中" :value="2" />
            <el-option label="已解决" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="检出时间">
          <el-date-picker
            v-model="timeRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            class="!w-64"
            @change="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="flex items-center justify-between mb-3">
      <span class="text-sm text-gray-500">
        共 <strong class="text-gray-700">{{ pagination.total }}</strong> 条告警记录
      </span>
      <el-button
        type="primary"
        size="small"
        :disabled="selectedIds.length === 0"
        :loading="batchLoading"
        @click="handleBatchRead"
      >批量标记已读</el-button>
    </div>

    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="alertList"
        border
        stripe
        highlight-current-row
        class="w-full"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="告警标题" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" :underline="false" @click="handleViewDetail(row)">
              {{ row.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column label="所属水库" width="140">
          <template #default="{ row }">
            {{ getReservoirName(row.reservoir_id) }}
          </template>
        </el-table-column>
        <el-table-column label="告警级别" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getLevelTagType(row.alert_level)" size="small" effect="dark">
              {{ levelLabels[row.alert_level] ?? row.alert_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="指标摘要" min-width="260">
          <template #default="{ row }">
            <div v-if="row.indicators && row.indicators.length" class="text-xs leading-relaxed">
              <div v-for="(indicator, idx) in row.indicators" :key="idx">
                {{ indicator.name }} {{ indicator.value }} &gt; {{ indicator.limit }}
              </div>
            </div>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column label="检出时间" width="160" align="center">
          <template #default="{ row }">
            {{ formatDateTime(row.detected_at) }}
          </template>
        </el-table-column>
        <el-table-column label="处理状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ statusLabels[row.status] ?? row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="处理人" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.handler_name" class="text-gray-700">{{ row.handler_name }}</span>
            <span v-else class="text-gray-400">未分配</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty
            :description="hasSearched ? '未找到匹配的告警记录' : '暂无预警记录，系统运行正常'"
          >
            <span v-if="hasSearched" class="text-xs text-gray-400">请调整筛选条件</span>
          </el-empty>
        </template>
      </el-table>

      <div class="flex justify-end mt-4">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
/**
 * 预警中心
 * 功能描述：全系统告警的统一管理列表页，支持按水库、级别、状态、时间筛选
 * 依赖组件：无
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, RefreshLeft } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/format'
import { getAlertList, getUnreadAlertCount, batchReadAlerts } from '@/api/alert'
import { getReservoirList } from '@/api/reservoir'

const loading = ref(false)
const hasSearched = ref(false)

const filter = reactive({
  reservoir_id: null,
  alert_level: null,
  status: null
})
const timeRange = ref(null)

const alertList = ref([])
const reservoirOptions = ref([])

const unreadCount = ref(0)
const selectedIds = ref([])
const batchLoading = ref(false)

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

const levelLabels = {
  1: '提示',
  2: '警告',
  3: '严重'
}

const levelTagTypeMap = {
  1: 'info',
  2: 'warning',
  3: 'danger'
}

const statusLabels = {
  0: '新增',
  1: '已确认',
  2: '处理中',
  3: '已解决'
}

const statusTagTypeMap = {
  0: '',
  1: 'warning',
  2: 'primary',
  3: 'success'
}

const getLevelTagType = (level) => levelTagTypeMap[level] ?? levelTagTypeMap[Number(level)] ?? 'info'
const getStatusTagType = (status) => statusTagTypeMap[status] || 'info'

const getReservoirName = (id) => {
  const item = reservoirOptions.value.find((r) => r.id === id)
  return item ? item.name : `ID:${id}`
}

const fetchReservoirOptions = async () => {
  try {
    const res = await getReservoirList({ page: 1, page_size: 9999 })
    reservoirOptions.value = res.data.lists || []
  } catch {
    reservoirOptions.value = []
  }
}

const toUndefined = (val) => (val === null || val === undefined || val === '') ? undefined : val

const buildParams = () => ({
  page: pagination.page,
  page_size: pagination.page_size,
  reservoir_id: toUndefined(filter.reservoir_id),
  alert_level: toUndefined(filter.alert_level),
  status: toUndefined(filter.status),
  start_time: timeRange.value?.[0] || undefined,
  end_time: timeRange.value?.[1] || undefined
})

const validateDateRange = () => {
  if (timeRange.value && timeRange.value[0] && timeRange.value[1]) {
    if (timeRange.value[1] < timeRange.value[0]) {
      ElMessage.warning('结束日期不能早于开始日期')
      return false
    }
  }
  return true
}

const fetchAlertList = async () => {
  if (!validateDateRange()) return
  loading.value = true
  hasSearched.value = true
  try {
    const res = await getAlertList(buildParams())
    alertList.value = res.data.lists || []
    pagination.total = res.data.pagination.total
    pagination.total_pages = res.data.pagination.total_pages
  } catch (e) {
    ElMessage.error(e.message || '获取预警列表失败')
    alertList.value = []
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchAlertList()
}

const handleReset = () => {
  filter.reservoir_id = null
  filter.alert_level = null
  filter.status = null
  timeRange.value = null
  handleSearch()
}

const handlePageChange = () => {
  fetchAlertList()
}

const handleSizeChange = () => {
  pagination.page = 1
  fetchAlertList()
}

const router = useRouter()

const handleViewDetail = (row) => {
  router.push(`/alerts/${row.id}`)
}

const handleSelectionChange = (rows) => {
  selectedIds.value = rows.map((r) => r.id)
}

const handleBatchRead = async () => {
  if (!selectedIds.value.length) return
  try {
    await ElMessageBox.confirm(
      `确认将选中的 ${selectedIds.value.length} 条预警标记为已读？`,
      '批量已读',
      { type: 'info' }
    )
    batchLoading.value = true
    await batchReadAlerts(selectedIds.value)
    ElMessage.success(`已成功将 ${selectedIds.value.length} 条预警标记为已读`)
    selectedIds.value = []
    await fetchAlertList()
    await fetchUnreadCount()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '操作失败')
    }
  } finally {
    batchLoading.value = false
  }
}

const fetchUnreadCount = async () => {
  try {
    const res = await getUnreadAlertCount()
    unreadCount.value = res.data.count
  } catch {
    // 静默失败
  }
}

onMounted(async () => {
  await fetchReservoirOptions()
  await fetchAlertList()
  await fetchUnreadCount()
})
</script>
