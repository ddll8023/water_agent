<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索指标名称"
          clearable
          class="w-48"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-input
          v-model="searchCode"
          placeholder="搜索指标编码"
          clearable
          class="w-44"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="filterCategory"
          placeholder="指标分类"
          clearable
          class="w-36"
          @change="handleSearch"
        >
          <el-option label="物理" value="物理" />
          <el-option label="化学" value="化学" />
          <el-option label="生物" value="生物" />
          <el-option label="综合" value="综合" />
        </el-select>
        <el-select
          v-model="filterIsCore"
          placeholder="指标类型"
          clearable
          class="w-32"
          @change="handleSearch"
        >
          <el-option label="核心指标" :value="1" />
          <el-option label="普通指标" :value="0" />
        </el-select>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新增指标
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="indicatorList"
      border
      stripe
      class="w-full"
    >
      <el-table-column prop="code" label="指标编码" min-width="110" />
      <el-table-column prop="name" label="指标名称" min-width="130" />
      <el-table-column prop="unit" label="单位" width="80" align="center">
        <template #default="{ row }">
          {{ row.unit || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="分类" width="80" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.category" size="small" effect="plain">
            {{ row.category }}
          </el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="标准限值" min-width="400">
        <template #default="{ row }">
          <div class="flex items-center gap-2 flex-wrap">
            <el-tag
              v-if="row.standard_limit_i_lower !== null || row.standard_limit_i_upper !== null"
              size="small"
              type="success"
            >Ⅰ {{ formatLimit(row.standard_limit_i_lower, row.standard_limit_i_upper) }}</el-tag>
            <el-tag
              v-if="row.standard_limit_ii_lower !== null || row.standard_limit_ii_upper !== null"
              size="small"
              type="success"
            >Ⅱ {{ formatLimit(row.standard_limit_ii_lower, row.standard_limit_ii_upper) }}</el-tag>
            <el-tag
              v-if="row.standard_limit_iii_lower !== null || row.standard_limit_iii_upper !== null"
              size="small"
              type="warning"
            >Ⅲ {{ formatLimit(row.standard_limit_iii_lower, row.standard_limit_iii_upper) }}</el-tag>
            <el-tag
              v-if="row.standard_limit_iv_lower !== null || row.standard_limit_iv_upper !== null"
              size="small"
              type="warning"
            >Ⅳ {{ formatLimit(row.standard_limit_iv_lower, row.standard_limit_iv_upper) }}</el-tag>
            <el-tag
              v-if="row.standard_limit_v_lower !== null || row.standard_limit_v_upper !== null"
              size="small"
              type="danger"
            >Ⅴ {{ formatLimit(row.standard_limit_v_lower, row.standard_limit_v_upper) }}</el-tag>
            <span v-if="!hasAnyLimit(row)">-</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="核心指标" width="90" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.is_core" type="danger" size="small">核心</el-tag>
          <el-tag v-else type="info" size="small" effect="plain">普通</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button type="danger" link size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无指标数据" />
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
      :title="isEditMode ? '编辑指标' : '新增指标'"
      width="640px"
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
            <el-form-item label="指标名称" prop="name">
              <el-input v-model="createForm.name" placeholder="请输入指标名称" maxlength="100" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="指标编码" prop="code">
              <el-input v-model="createForm.code" placeholder="请输入指标编码" maxlength="50" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="单位" prop="unit">
              <el-input v-model="createForm.unit" placeholder="如：mg/L" maxlength="50" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-select v-model="createForm.category" placeholder="请选择分类" clearable class="w-full">
                <el-option label="物理" value="物理" />
                <el-option label="化学" value="化学" />
                <el-option label="生物" value="生物" />
                <el-option label="综合" value="综合" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="核心指标" prop="is_core">
          <el-radio-group v-model="createForm.is_core">
            <el-radio :value="1">是</el-radio>
            <el-radio :value="0">否</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-divider content-position="left">标准限值（下限 ~ 上限）</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Ⅰ类下限" prop="standard_limit_i_lower">
              <el-input-number
                v-model="createForm.standard_limit_i_lower"
                :min="0"
                :max="999999"
                :precision="4"
                controls-position="right"
                class="w-full"
                placeholder="Ⅰ类下限"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Ⅰ类上限" prop="standard_limit_i_upper">
              <el-input-number
                v-model="createForm.standard_limit_i_upper"
                :min="0"
                :max="999999"
                :precision="4"
                controls-position="right"
                class="w-full"
                placeholder="Ⅰ类上限"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Ⅱ类下限" prop="standard_limit_ii_lower">
              <el-input-number
                v-model="createForm.standard_limit_ii_lower"
                :min="0"
                :max="999999"
                :precision="4"
                controls-position="right"
                class="w-full"
                placeholder="Ⅱ类下限"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Ⅱ类上限" prop="standard_limit_ii_upper">
              <el-input-number
                v-model="createForm.standard_limit_ii_upper"
                :min="0"
                :max="999999"
                :precision="4"
                controls-position="right"
                class="w-full"
                placeholder="Ⅱ类上限"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Ⅲ类下限" prop="standard_limit_iii_lower">
              <el-input-number
                v-model="createForm.standard_limit_iii_lower"
                :min="0"
                :max="999999"
                :precision="4"
                controls-position="right"
                class="w-full"
                placeholder="Ⅲ类下限"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Ⅲ类上限" prop="standard_limit_iii_upper">
              <el-input-number
                v-model="createForm.standard_limit_iii_upper"
                :min="0"
                :max="999999"
                :precision="4"
                controls-position="right"
                class="w-full"
                placeholder="Ⅲ类上限"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Ⅳ类下限" prop="standard_limit_iv_lower">
              <el-input-number
                v-model="createForm.standard_limit_iv_lower"
                :min="0"
                :max="999999"
                :precision="4"
                controls-position="right"
                class="w-full"
                placeholder="Ⅳ类下限"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Ⅳ类上限" prop="standard_limit_iv_upper">
              <el-input-number
                v-model="createForm.standard_limit_iv_upper"
                :min="0"
                :max="999999"
                :precision="4"
                controls-position="right"
                class="w-full"
                placeholder="Ⅳ类上限"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Ⅴ类下限" prop="standard_limit_v_lower">
              <el-input-number
                v-model="createForm.standard_limit_v_lower"
                :min="0"
                :max="999999"
                :precision="4"
                controls-position="right"
                class="w-full"
                placeholder="Ⅴ类下限"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Ⅴ类上限" prop="standard_limit_v_upper">
              <el-input-number
                v-model="createForm.standard_limit_v_upper"
                :min="0"
                :max="999999"
                :precision="4"
                controls-position="right"
                class="w-full"
                placeholder="Ⅴ类上限"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreateIndicator">
          {{ isEditMode ? '保 存' : '确 定' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 监测指标管理 Tab
 * 功能描述：指标列表查询、筛选、分页、新增、编辑
 * 依赖组件：无
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { getIndicatorList, createIndicator, getIndicatorDetail, updateIndicator, deleteIndicator } from '@/api/indicator'

const loading = ref(false)
const searchKeyword = ref('')
const searchCode = ref('')
const filterCategory = ref(null)
const filterIsCore = ref(null)

const indicatorList = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0,
  total_pages: 0
})

const fetchIndicatorList = async () => {
  loading.value = true
  try {
    const params = {
      name: searchKeyword.value || undefined,
      code: searchCode.value || undefined,
      category: filterCategory.value || undefined,
      is_core: filterIsCore.value !== null && filterIsCore.value !== undefined ? filterIsCore.value : undefined,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const res = await getIndicatorList(params)
    indicatorList.value = res.data.lists
    pagination.total = res.data.pagination.total
    pagination.total_pages = res.data.pagination.total_pages
  } catch (e) {
    ElMessage.error(e.message || '获取指标列表失败')
    indicatorList.value = []
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchIndicatorList()
}

const handlePageChange = () => {
  fetchIndicatorList()
}

const handleSizeChange = () => {
  pagination.page = 1
  fetchIndicatorList()
}

onMounted(() => {
  fetchIndicatorList()
})

const createDialogVisible = ref(false)
const createLoading = ref(false)
const createFormRef = ref(null)
const isEditMode = ref(false)
const editingIndicatorId = ref(null)

const createForm = reactive({
  name: '',
  code: '',
  unit: '',
  category: '',
  standard_limit_i_lower: null,
  standard_limit_i_upper: null,
  standard_limit_ii_lower: null,
  standard_limit_ii_upper: null,
  standard_limit_iii_lower: null,
  standard_limit_iii_upper: null,
  standard_limit_iv_lower: null,
  standard_limit_iv_upper: null,
  standard_limit_v_lower: null,
  standard_limit_v_upper: null,
  is_core: 0
})

const createFormRules = {
  name: [
    { required: true, message: '请输入指标名称', trigger: 'blur' },
    { max: 100, message: '指标名称不超过100个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入指标编码', trigger: 'blur' },
    { max: 50, message: '指标编码不超过50个字符', trigger: 'blur' }
  ]
}

const openCreateDialog = () => {
  isEditMode.value = false
  editingIndicatorId.value = null
  createDialogVisible.value = true
}

const openEditDialog = async (row) => {
  isEditMode.value = true
  editingIndicatorId.value = row.id
  createLoading.value = true
  createDialogVisible.value = true
  try {
    const res = await getIndicatorDetail(row.id)
    const detail = res.data
    createForm.name = detail.name
    createForm.code = detail.code
    createForm.unit = detail.unit || ''
    createForm.category = detail.category || ''
    createForm.standard_limit_i_lower = detail.standard_limit_i_lower ?? null
    createForm.standard_limit_i_upper = detail.standard_limit_i_upper ?? null
    createForm.standard_limit_ii_lower = detail.standard_limit_ii_lower ?? null
    createForm.standard_limit_ii_upper = detail.standard_limit_ii_upper ?? null
    createForm.standard_limit_iii_lower = detail.standard_limit_iii_lower ?? null
    createForm.standard_limit_iii_upper = detail.standard_limit_iii_upper ?? null
    createForm.standard_limit_iv_lower = detail.standard_limit_iv_lower ?? null
    createForm.standard_limit_iv_upper = detail.standard_limit_iv_upper ?? null
    createForm.standard_limit_v_lower = detail.standard_limit_v_lower ?? null
    createForm.standard_limit_v_upper = detail.standard_limit_v_upper ?? null
    createForm.is_core = detail.is_core ?? 0
  } catch (e) {
    ElMessage.error(e.message || '获取指标详情失败')
    createDialogVisible.value = false
  } finally {
    createLoading.value = false
  }
}

const resetCreateForm = () => {
  isEditMode.value = false
  editingIndicatorId.value = null
  createForm.name = ''
  createForm.code = ''
  createForm.unit = ''
  createForm.category = ''
  createForm.standard_limit_i_lower = null
  createForm.standard_limit_i_upper = null
  createForm.standard_limit_ii_lower = null
  createForm.standard_limit_ii_upper = null
  createForm.standard_limit_iii_lower = null
  createForm.standard_limit_iii_upper = null
  createForm.standard_limit_iv_lower = null
  createForm.standard_limit_iv_upper = null
  createForm.standard_limit_v_lower = null
  createForm.standard_limit_v_upper = null
  createForm.is_core = 0
  createFormRef.value?.clearValidate()
}

const handleCreateIndicator = async () => {
  if (!createFormRef.value) return
  try {
    await createFormRef.value.validate()
  } catch {
    return
  }
  createLoading.value = true
  try {
    const rawPayload = {
      name: createForm.name,
      code: createForm.code,
      unit: createForm.unit || undefined,
      category: createForm.category || undefined,
      standard_limit_i_lower: createForm.standard_limit_i_lower ?? undefined,
      standard_limit_i_upper: createForm.standard_limit_i_upper ?? undefined,
      standard_limit_ii_lower: createForm.standard_limit_ii_lower ?? undefined,
      standard_limit_ii_upper: createForm.standard_limit_ii_upper ?? undefined,
      standard_limit_iii_lower: createForm.standard_limit_iii_lower ?? undefined,
      standard_limit_iii_upper: createForm.standard_limit_iii_upper ?? undefined,
      standard_limit_iv_lower: createForm.standard_limit_iv_lower ?? undefined,
      standard_limit_iv_upper: createForm.standard_limit_iv_upper ?? undefined,
      standard_limit_v_lower: createForm.standard_limit_v_lower ?? undefined,
      standard_limit_v_upper: createForm.standard_limit_v_upper ?? undefined,
      is_core: createForm.is_core
    }
    const payload = Object.fromEntries(
      Object.entries(rawPayload).filter(([_, v]) => v !== undefined)
    )
    if (isEditMode.value) {
      await updateIndicator(editingIndicatorId.value, payload)
      ElMessage.success('指标更新成功')
    } else {
      await createIndicator(payload)
      ElMessage.success('指标创建成功')
    }
    createDialogVisible.value = false
    pagination.page = 1
    await fetchIndicatorList()
  } catch (e) {
    ElMessage.error(e.message || (isEditMode.value ? '更新指标失败' : '创建指标失败'))
  } finally {
    createLoading.value = false
  }
}

const formatLimit = (lower, upper) => {
  if (lower !== null && upper !== null) return `${lower}~${upper}`
  if (lower !== null) return `≥${lower}`
  if (upper !== null) return `≤${upper}`
  return ''
}

const hasAnyLimit = (row) => {
  const classes = ['i', 'ii', 'iii', 'iv', 'v']
  return classes.some((c) => row[`standard_limit_${c}_lower`] !== null || row[`standard_limit_${c}_upper`] !== null)
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该指标吗？删除后不可恢复。', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    await deleteIndicator(id)
    ElMessage.success('指标删除成功')
    await fetchIndicatorList()
  } catch (e) {
    ElMessage.error(e.message || '删除指标失败')
  }
}
</script>