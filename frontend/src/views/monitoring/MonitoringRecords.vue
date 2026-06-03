<template>
  <div>
    <div class="flex items-center justify-between mb-4 flex-wrap gap-3">
      <div class="flex items-center gap-3 flex-wrap">
        <el-select
          v-model="filterReservoirId"
          placeholder="所属水库"
          clearable
          filterable
          class="!w-44"
          @change="handleReservoirChange"
        >
          <el-option
            v-for="item in reservoirOptions"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-select
          v-model="filterStationId"
          placeholder="所属站点"
          clearable
          filterable
          class="!w-44"
          @change="handleSearch"
        >
          <el-option
            v-for="item in stationOptions"
            :key="item.id"
            :label="`${item.name}（${item.code}）`"
            :value="item.id"
          />
        </el-select>
        <el-select
          v-model="filterIndicatorId"
          placeholder="监测指标"
          clearable
          filterable
          class="!w-40"
          @change="handleSearch"
        >
          <el-option
            v-for="item in indicatorOptions"
            :key="item.id"
            :label="`${item.name}（${item.code}）`"
            :value="item.id"
          />
        </el-select>
        <el-select
          v-model="filterQualityFlag"
          placeholder="数据质量"
          clearable
          class="!w-32"
          @change="handleSearch"
        >
          <el-option label="可疑" :value="0" />
          <el-option label="正常" :value="1" />
          <el-option label="无效" :value="2" />
        </el-select>
        <el-date-picker
          v-model="timeRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          value-format="YYYY-MM-DD HH:mm:ss"
          class="!w-96"
          @change="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button @click="handleReset">
          <el-icon><RefreshLeft /></el-icon>
          重置
        </el-button>
      </div>
      <el-button type="primary" @click="openManualDialog">
        <el-icon><EditPen /></el-icon>
        人工录入
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="recordList"
      border
      stripe
      class="w-full"
    >
      <el-table-column prop="id" label="记录ID" width="90" align="center" />
      <el-table-column label="所属水库" min-width="140">
        <template #default="{ row }">
          {{ getReservoirName(row.reservoir_id) }}
        </template>
      </el-table-column>
      <el-table-column label="所属站点" min-width="180">
        <template #default="{ row }">
          {{ getStationName(row.station_id) }}
        </template>
      </el-table-column>
      <el-table-column label="监测指标" min-width="150">
        <template #default="{ row }">
          <div class="flex items-center gap-2">
            <span>{{ getIndicatorName(row.indicator_id) }}</span>
            <span v-if="getIndicatorUnit(row.indicator_id)" class="text-gray-400 text-xs">
              ({{ getIndicatorUnit(row.indicator_id) }})
            </span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="value" label="监测值" width="120" align="right">
        <template #default="{ row }">
          <span class="font-mono">{{ row.value }}</span>
        </template>
      </el-table-column>
      <el-table-column label="监测时间" width="170" align="center">
        <template #default="{ row }">
          {{ formatDateTime(row.record_time) }}
        </template>
      </el-table-column>
      <el-table-column label="数据质量" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.quality_flag !== null && row.quality_flag !== undefined" :type="getQualityTagType(row.quality_flag)" size="small">
            {{ qualityFlagLabels[row.quality_flag] ?? '-' }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="handleViewRealtime(row)">
            查看实时
          </el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无监测记录" />
      </template>
    </el-table>

    <div class="flex justify-end mt-4">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 15, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <el-dialog
      v-model="manualDialogVisible"
      title="人工采样录入"
      width="520px"
      :close-on-click-modal="false"
      @close="resetManualForm"
    >
      <el-form
        ref="manualFormRef"
        :model="manualForm"
        :rules="manualFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="所属水库" prop="reservoir_id">
          <el-select
            v-model="manualForm.reservoir_id"
            placeholder="请选择水库"
            filterable
            class="w-full"
            @change="handleManualReservoirChange"
          >
            <el-option
              v-for="item in reservoirOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属站点" prop="station_id">
          <el-select
            v-model="manualForm.station_id"
            placeholder="请选择站点"
            filterable
            class="w-full"
          >
            <el-option
              v-for="item in manualStationOptions"
              :key="item.id"
              :label="`${item.name}（${item.code}）`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="监测指标" prop="indicator_id">
          <el-select
            v-model="manualForm.indicator_id"
            placeholder="请选择指标"
            filterable
            class="w-full"
          >
            <el-option
              v-for="item in indicatorOptions"
              :key="item.id"
              :label="`${item.name}（${item.code}）`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="监测值" prop="value">
          <el-input-number
            v-model="manualForm.value"
            :min="-999999"
            :max="999999"
            :precision="4"
            controls-position="right"
            class="w-full"
            placeholder="请输入监测值"
          />
        </el-form-item>
        <el-form-item label="监测时间" prop="record_time">
          <el-date-picker
            v-model="manualForm.record_time"
            type="datetime"
            placeholder="请选择监测时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            class="w-full"
          />
        </el-form-item>
        <el-form-item label="数据质量" prop="quality_flag">
          <el-select v-model="manualForm.quality_flag" class="w-full">
            <el-option label="正常" :value="1" />
            <el-option label="可疑" :value="0" />
            <el-option label="无效" :value="2" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="manualDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="manualSubmitLoading" @click="handleManualSubmit">
          确 定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 监测数据记录页
 * 功能描述：监测记录列表查询、多条件筛选、分页
 * 依赖组件：无
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, RefreshLeft, EditPen } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/format'
import { getMonitoringRecordsList, submitManualRecord } from '@/api/monitoring'
import { getReservoirList } from '@/api/reservoir'
import { getStationList } from '@/api/station'
import { getIndicatorList } from '@/api/indicator'

const loading = ref(false)
const filterReservoirId = ref(null)
const filterStationId = ref(null)
const filterIndicatorId = ref(null)
const filterQualityFlag = ref(null)
const timeRange = ref(null)

const recordList = ref([])
const reservoirOptions = ref([])
const stationOptions = ref([])
const indicatorOptions = ref([])

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0,
  total_pages: 0
})

const qualityFlagLabels = {
  0: '可疑',
  1: '正常',
  2: '无效'
}

const getQualityTagType = (flag) => {
  const map = { 0: 'warning', 1: 'success', 2: 'danger' }
  return map[flag] || 'info'
}

const getReservoirName = (id) => {
  const item = reservoirOptions.value.find((r) => r.id === id)
  return item ? item.name : `ID:${id}`
}

const getStationName = (id) => {
  const item = stationOptions.value.find((s) => s.id === id)
  return item ? item.name : `ID:${id}`
}

const getIndicatorName = (id) => {
  const item = indicatorOptions.value.find((i) => i.id === id)
  return item ? item.name : `ID:${id}`
}

const getIndicatorUnit = (id) => {
  const item = indicatorOptions.value.find((i) => i.id === id)
  return item?.unit || ''
}

const fetchReservoirOptions = async () => {
  try {
    const res = await getReservoirList({ page: 1, page_size: 9999 })
    reservoirOptions.value = res.data.lists || []
  } catch {
    reservoirOptions.value = []
  }
}

const fetchStationOptions = async (reservoirId) => {
  try {
    const res = await getStationList({
      reservoir_id: reservoirId || undefined,
      page: 1,
      page_size: 9999
    })
    stationOptions.value = res.data.lists || []
  } catch {
    stationOptions.value = []
  }
}

const fetchIndicatorOptions = async () => {
  try {
    const res = await getIndicatorList({ page: 1, page_size: 9999 })
    indicatorOptions.value = res.data.lists || []
  } catch {
    indicatorOptions.value = []
  }
}

const buildParams = () => ({
  reservoir_id: filterReservoirId.value || undefined,
  station_id: filterStationId.value || undefined,
  indicator_id: filterIndicatorId.value || undefined,
  quality_flag:
    filterQualityFlag.value !== null && filterQualityFlag.value !== undefined
      ? filterQualityFlag.value
      : undefined,
  start_time: timeRange.value?.[0] || undefined,
  end_time: timeRange.value?.[1] || undefined,
  page: pagination.page,
  page_size: pagination.page_size
})

const fetchRecordList = async () => {
  loading.value = true
  try {
    const res = await getMonitoringRecordsList(buildParams())
    recordList.value = res.data.lists || []
    pagination.total = res.data.pagination.total
    pagination.total_pages = res.data.pagination.total_pages
  } catch (e) {
    ElMessage.error(e.message || '获取监测记录失败')
    recordList.value = []
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchRecordList()
}

const handleReservoirChange = () => {
  filterStationId.value = null
  handleSearch()
}

const handlePageChange = () => {
  fetchRecordList()
}

const handleSizeChange = () => {
  pagination.page = 1
  fetchRecordList()
}

const handleReset = () => {
  filterReservoirId.value = null
  filterStationId.value = null
  filterIndicatorId.value = null
  filterQualityFlag.value = null
  timeRange.value = null
  handleSearch()
}

const router = useRouter()

const handleViewRealtime = (row) => {
  router.push(`/monitoring/reservoirs/${row.reservoir_id}`)
}

onMounted(async () => {
  await Promise.all([
    fetchReservoirOptions(),
    fetchStationOptions(),
    fetchIndicatorOptions()
  ])
  await fetchRecordList()
})

/* ===== 人工采样录入 ===== */

const manualDialogVisible = ref(false)
const manualSubmitLoading = ref(false)
const manualFormRef = ref(null)
const manualStationOptions = ref([])

const manualForm = reactive({
  reservoir_id: null,
  station_id: null,
  indicator_id: null,
  value: null,
  record_time: '',
  quality_flag: 1
})

const manualFormRules = {
  reservoir_id: [{ required: true, message: '请选择水库', trigger: 'change' }],
  station_id: [{ required: true, message: '请选择站点', trigger: 'change' }],
  indicator_id: [{ required: true, message: '请选择指标', trigger: 'change' }],
  value: [{ required: true, message: '请输入监测值', trigger: 'blur' }],
  record_time: [{ required: true, message: '请选择监测时间', trigger: 'change' }]
}

const openManualDialog = () => {
  manualForm.record_time = formatDateTime(new Date())
  manualDialogVisible.value = true
}

const handleManualReservoirChange = async (id) => {
  manualForm.station_id = null
  manualStationOptions.value = []
  if (!id) return
  try {
    const res = await getStationList({ reservoir_id: id, page: 1, page_size: 9999 })
    manualStationOptions.value = res.data.lists || []
  } catch {
    manualStationOptions.value = []
  }
}

const resetManualForm = () => {
  manualForm.reservoir_id = null
  manualForm.station_id = null
  manualForm.indicator_id = null
  manualForm.value = null
  manualForm.record_time = ''
  manualForm.quality_flag = 1
  manualStationOptions.value = []
  manualFormRef.value?.clearValidate()
}

const handleManualSubmit = async () => {
  if (!manualFormRef.value) return
  try {
    await manualFormRef.value.validate()
  } catch {
    return
  }
  manualSubmitLoading.value = true
  try {
    await submitManualRecord({
      station_id: manualForm.station_id,
      indicator_id: manualForm.indicator_id,
      value: manualForm.value,
      record_time: manualForm.record_time,
      quality_flag: manualForm.quality_flag
    })
    ElMessage.success('录入成功')
    manualDialogVisible.value = false
    await fetchRecordList()
  } catch (e) {
    ElMessage.error(e.message || '录入失败')
  } finally {
    manualSubmitLoading.value = false
  }
}
</script>
