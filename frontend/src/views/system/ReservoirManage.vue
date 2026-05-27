<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索水库名称、编号"
          clearable
          class="w-64"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="filterWatershed"
          placeholder="所属流域"
          clearable
          class="w-40"
        >
          <el-option label="长江流域" value="长江流域" />
          <el-option label="黄河流域" value="黄河流域" />
          <el-option label="珠江流域" value="珠江流域" />
          <el-option label="淮河流域" value="淮河流域" />
          <el-option label="海河流域" value="海河流域" />
          <el-option label="松花江流域" value="松花江流域" />
        </el-select>
        <el-select
          v-model="filterWaterGrade"
          placeholder="水质等级"
          clearable
          class="w-36"
        >
          <el-option label="Ⅰ类" value="Ⅰ类" />
          <el-option label="Ⅱ类" value="Ⅱ类" />
          <el-option label="Ⅲ类" value="Ⅲ类" />
          <el-option label="Ⅳ类" value="Ⅳ类" />
          <el-option label="Ⅴ类" value="Ⅴ类" />
        </el-select>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新增水库
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="reservoirList"
      border
      stripe
      class="w-full"
      empty-text="暂无水库数据"
    >
      <el-table-column prop="code" label="水库编号" min-width="120" />
      <el-table-column prop="name" label="水库名称" min-width="140" />
      <el-table-column prop="capacity" label="库容(万m³)" min-width="110">
        <template #default="{ row }">
          {{ row.capacity || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="水质等级" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.water_grade" :type="getWaterGradeTagType(row.water_grade)" size="small">
            {{ row.water_grade }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="watershed" label="所属流域" min-width="120">
        <template #default="{ row }">
          {{ row.watershed || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="创建时间" min-width="170">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small">编辑</el-button>
          <el-button type="danger" link size="small">删除</el-button>
        </template>
      </el-table-column>
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
      title="新增水库"
      width="600px"
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
            <el-form-item label="水库名称" prop="name">
              <el-input v-model="createForm.name" placeholder="请输入水库名称" maxlength="100" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="水库编号" prop="code">
              <el-input v-model="createForm.code" placeholder="请输入水库编号" maxlength="50" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="所在位置" prop="location">
              <el-input v-model="createForm.location" placeholder="请输入所在位置" maxlength="200" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属流域" prop="watershed">
              <el-select v-model="createForm.watershed" placeholder="请选择所属流域" clearable class="w-full">
                <el-option label="长江流域" value="长江流域" />
                <el-option label="黄河流域" value="黄河流域" />
                <el-option label="珠江流域" value="珠江流域" />
                <el-option label="淮河流域" value="淮河流域" />
                <el-option label="海河流域" value="海河流域" />
                <el-option label="松花江流域" value="松花江流域" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
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
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="库容(万m³)" prop="capacity">
              <el-input v-model="createForm.capacity" placeholder="请输入库容" maxlength="50" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="水质等级" prop="water_grade">
              <el-select v-model="createForm.water_grade" placeholder="请选择水质等级" clearable class="w-full">
                <el-option label="Ⅰ类" value="Ⅰ类" />
                <el-option label="Ⅱ类" value="Ⅱ类" />
                <el-option label="Ⅲ类" value="Ⅲ类" />
                <el-option label="Ⅳ类" value="Ⅳ类" />
                <el-option label="Ⅴ类" value="Ⅴ类" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="createForm.sort_order" :min="0" :max="9999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreateReservoir">确 定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 水库管理页
 * 功能描述：水库列表查询、筛选与分页展示
 * 依赖组件：无
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { getReservoirList, createReservoir } from '@/api/reservoir'

const loading = ref(false)
const searchKeyword = ref('')
const filterWatershed = ref(null)
const filterWaterGrade = ref(null)

const reservoirList = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0,
  total_pages: 0
})

const getWaterGradeTagType = (grade) => {
  const typeMap = {
    'Ⅰ类': 'success',
    'Ⅱ类': 'success',
    'Ⅲ类': 'warning',
    'Ⅳ类': 'warning',
    'Ⅴ类': 'danger'
  }
  return typeMap[grade] || 'info'
}

const formatDateTime = (value) => {
  if (!value) return '-'
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const fetchReservoirList = async () => {
  loading.value = true
  try {
    const params = {
      keyword: searchKeyword.value || undefined,
      watershed: filterWatershed.value || undefined,
      water_grade: filterWaterGrade.value || undefined,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const res = await getReservoirList(params)
    reservoirList.value = res.data.lists
    pagination.total = res.data.pagination.total
    pagination.total_pages = res.data.pagination.total_pages
  } catch (e) {
    ElMessage.error(e.message || '获取水库列表失败')
    reservoirList.value = []
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchReservoirList()
}

const handlePageChange = () => {
  fetchReservoirList()
}

const handleSizeChange = () => {
  pagination.page = 1
  fetchReservoirList()
}

onMounted(() => {
  fetchReservoirList()
})

const createDialogVisible = ref(false)
const createLoading = ref(false)
const createFormRef = ref(null)

const createForm = reactive({
  name: '',
  code: '',
  location: '',
  longitude: '',
  latitude: '',
  capacity: '',
  water_grade: '',
  watershed: '',
  sort_order: 0
})

const createFormRules = {
  name: [
    { required: true, message: '请输入水库名称', trigger: 'blur' },
    { max: 100, message: '水库名称不超过100个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入水库编号', trigger: 'blur' },
    { max: 50, message: '水库编号不超过50个字符', trigger: 'blur' }
  ]
}

const openCreateDialog = () => {
  createDialogVisible.value = true
}

const resetCreateForm = () => {
  createForm.name = ''
  createForm.code = ''
  createForm.location = ''
  createForm.longitude = ''
  createForm.latitude = ''
  createForm.capacity = ''
  createForm.water_grade = ''
  createForm.watershed = ''
  createForm.sort_order = 0
  createFormRef.value?.clearValidate()
}

const handleCreateReservoir = async () => {
  if (!createFormRef.value) return
  try {
    await createFormRef.value.validate()
  } catch {
    return
  }
  createLoading.value = true
  try {
    const payload = {
      name: createForm.name,
      code: createForm.code,
      location: createForm.location || undefined,
      longitude: createForm.longitude || undefined,
      latitude: createForm.latitude || undefined,
      capacity: createForm.capacity || undefined,
      water_grade: createForm.water_grade || undefined,
      watershed: createForm.watershed || undefined,
      sort_order: createForm.sort_order
    }
    await createReservoir(payload)
    ElMessage.success('水库创建成功')
    createDialogVisible.value = false
    pagination.page = 1
    await fetchReservoirList()
  } catch (e) {
    ElMessage.error(e.message || '创建水库失败')
  } finally {
    createLoading.value = false
  }
}
</script>
