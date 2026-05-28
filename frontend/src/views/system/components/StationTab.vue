<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <el-select
          v-model="filterReservoirId"
          placeholder="所属水库"
          clearable
          class="w-48"
          @change="handleSearch"
        >
          <el-option
            v-for="item in reservoirOptions"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索站点名称"
          clearable
          class="w-56"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新增站点
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="stationList"
      border
      stripe
      class="w-full"
    >
      <el-table-column prop="name" label="站点名称" min-width="130" />
      <el-table-column prop="code" label="站点编码" min-width="120" />
      <el-table-column label="所属水库" min-width="130">
        <template #default="{ row }">
          {{ getReservoirName(row.reservoir_id) }}
        </template>
      </el-table-column>
      <el-table-column label="站点类型" width="110" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.type" :type="getTypeTagType(row.type)" size="small">
            {{ typeLabels[row.type] || row.type }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="sampling_point" label="采样点位" min-width="150">
        <template #default="{ row }">
          {{ row.sampling_point || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="最后数据时间" width="170" align="center">
        <template #default="{ row }">
          {{ row.last_data_time || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="运行状态" width="120" align="center">
        <template #default="{ row }">
          <div class="flex items-center justify-center gap-1">
            <span
              class="inline-block w-2 h-2 rounded-full"
              :class="row.status === 1 ? 'bg-green-500' : 'bg-gray-400'"
            />
            <span>{{ row.status === 1 ? '在线' : '离线' }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button type="danger" link size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无站点数据" />
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
      v-model="createDialogVisible"
      title="新增监测站点"
      width="580px"
      :close-on-click-modal="false"
      @close="resetCreateForm"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="站点名称" prop="name">
              <el-input v-model="createForm.name" placeholder="请输入站点名称" maxlength="100" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="站点编码" prop="code">
              <el-input v-model="createForm.code" placeholder="请输入站点编码" maxlength="50" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="所属水库" prop="reservoir_id">
          <el-select v-model="createForm.reservoir_id" placeholder="请选择所属水库" clearable class="w-full">
            <el-option
              v-for="item in reservoirOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="站点类型" prop="type">
          <el-radio-group v-model="createForm.type">
            <el-radio value="auto">自动站</el-radio>
            <el-radio value="manual">人工站</el-radio>
            <el-radio value="sensing">遥感站</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="经度" prop="longitude">
              <el-input v-model="createForm.longitude" placeholder="如：110.123456" maxlength="50" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="纬度" prop="latitude">
              <el-input v-model="createForm.latitude" placeholder="如：30.123456" maxlength="50" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="采样点位" prop="sampling_point">
          <el-input v-model="createForm.sampling_point" placeholder="请输入采样点位描述" maxlength="255" />
        </el-form-item>
        <el-form-item label="运行状态" prop="status" v-if="isEditMode">
          <el-radio-group v-model="createForm.status">
            <el-radio :value="1">在线</el-radio>
            <el-radio :value="0">离线</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreateStation">
          {{ isEditMode ? '保 存' : '确 定' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 监测站点管理 Tab
 * 功能描述：监测站点列表查询、筛选、分页、新增、编辑
 * 依赖组件：无
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { getStationList, createStation, getStationDetail, updateStation, deleteStation } from '@/api/station'
import { getReservoirList } from '@/api/reservoir'

const loading = ref(false)
const searchKeyword = ref('')
const filterReservoirId = ref(null)
const reservoirOptions = ref([])

const stationList = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0,
  total_pages: 0
})

const typeLabels = {
  auto: '自动站',
  manual: '人工站',
  sensing: '遥感站'
}

const getTypeTagType = (type) => {
  const typeMap = {
    auto: 'success',
    manual: 'warning',
    sensing: 'info'
  }
  return typeMap[type] || 'info'
}

const getReservoirName = (reservoirId) => {
  const item = reservoirOptions.value.find((r) => r.id === reservoirId)
  return item ? item.name : `ID:${reservoirId}`
}

const fetchReservoirOptions = async () => {
  try {
    const res = await getReservoirList({ page: 1, page_size: 9999 })
    reservoirOptions.value = res.data.lists || []
  } catch {
    reservoirOptions.value = []
  }
}

const fetchStationList = async () => {
  loading.value = true
  try {
    const params = {
      keyword: searchKeyword.value || undefined,
      reservoir_id: filterReservoirId.value || undefined,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const res = await getStationList(params)
    stationList.value = res.data.lists
    pagination.total = res.data.pagination.total
    pagination.total_pages = res.data.pagination.total_pages
  } catch (e) {
    if (e.message !== '获取站点列表失败') {
      ElMessage.error(e.message || '请求失败')
    }
    stationList.value = []
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchStationList()
}

const handlePageChange = () => {
  fetchStationList()
}

const handleSizeChange = () => {
  pagination.page = 1
  fetchStationList()
}

onMounted(() => {
  fetchReservoirOptions()
  fetchStationList()
})

const createDialogVisible = ref(false)
const createLoading = ref(false)
const createFormRef = ref(null)
const isEditMode = ref(false)
const editingStationId = ref(null)

const createForm = reactive({
  name: '',
  code: '',
  reservoir_id: null,
  type: 'auto',
  longitude: '',
  latitude: '',
  sampling_point: '',
  status: 1
})

const createFormRules = {
  name: [
    { required: true, message: '请输入站点名称', trigger: 'blur' },
    { max: 100, message: '站点名称不超过100个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入站点编码', trigger: 'blur' },
    { max: 50, message: '站点编码不超过50个字符', trigger: 'blur' }
  ],
  reservoir_id: [
    { required: true, message: '请选择所属水库', trigger: 'change' }
  ]
}

const openCreateDialog = () => {
  isEditMode.value = false
  editingStationId.value = null
  fetchReservoirOptions()
  createDialogVisible.value = true
}

const openEditDialog = async (row) => {
  isEditMode.value = true
  editingStationId.value = row.id
  createLoading.value = true
  createDialogVisible.value = true
  await fetchReservoirOptions()
  try {
    const res = await getStationDetail(row.id)
    const detail = res.data
    createForm.name = detail.name
    createForm.code = detail.code
    createForm.reservoir_id = detail.reservoir_id
    createForm.type = detail.type || 'auto'
    createForm.longitude = detail.longitude || ''
    createForm.latitude = detail.latitude || ''
    createForm.sampling_point = detail.sampling_point || ''
    createForm.status = detail.status
  } catch {
    ElMessage.error('获取站点详情失败')
    createDialogVisible.value = false
  } finally {
    createLoading.value = false
  }
}

const resetCreateForm = () => {
  isEditMode.value = false
  editingStationId.value = null
  createForm.name = ''
  createForm.code = ''
  createForm.reservoir_id = null
  createForm.type = 'auto'
  createForm.longitude = ''
  createForm.latitude = ''
  createForm.sampling_point = ''
  createForm.status = 1
  createFormRef.value?.clearValidate()
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该监测站点吗？删除后不可恢复。', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    await deleteStation(id)
    ElMessage.success('站点删除成功')
    await fetchStationList()
  } catch (e) {
    ElMessage.error(e.message || '删除站点失败')
  }
}

const handleCreateStation = async () => {
  if (!createFormRef.value) return
  try {
    await createFormRef.value.validate()
  } catch {
    return
  }
  createLoading.value = true
  try {
    const payload = {
      reservoir_id: createForm.reservoir_id,
      name: createForm.name,
      code: createForm.code,
      type: createForm.type || undefined,
      longitude: createForm.longitude || undefined,
      latitude: createForm.latitude || undefined,
      sampling_point: createForm.sampling_point || undefined
    }
    if (isEditMode.value) {
      payload.status = createForm.status
      await updateStation(editingStationId.value, payload)
      ElMessage.success('站点更新成功')
    } else {
      await createStation(payload)
      ElMessage.success('站点创建成功')
    }
    createDialogVisible.value = false
    pagination.page = 1
    await fetchStationList()
  } catch (e) {
    ElMessage.error(e.message || (isEditMode.value ? '更新站点失败' : '创建站点失败'))
  } finally {
    createLoading.value = false
  }
}
</script>
