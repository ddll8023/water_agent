<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-3">
        <el-select
          v-model="filterIndicatorId"
          placeholder="关联指标"
          clearable
          class="w-36"
          @change="handleSearch"
        >
          <el-option
            v-for="item in indicatorOptions"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-select
          v-model="filterReservoirId"
          placeholder="适用水库"
          clearable
          class="w-36"
          @change="handleSearch"
        >
          <el-option label="全局规则" :value="-1" />
          <el-option
            v-for="item in reservoirOptions"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-select
          v-model="filterIsActive"
          placeholder="启用状态"
          clearable
          class="w-32"
          @change="handleSearch"
        >
          <el-option label="已启用" :value="1" />
          <el-option label="已禁用" :value="0" />
        </el-select>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新增规则
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="ruleList"
      border
      stripe
      class="w-full"
    >
      <el-table-column prop="rule_name" label="规则名称" min-width="150" />
      <el-table-column label="关联指标" width="120">
        <template #default="{ row }">
          {{ getIndicatorName(row.indicator_id) }}
        </template>
      </el-table-column>
      <el-table-column label="适用水库" width="120">
        <template #default="{ row }">
          <span v-if="row.reservoir_id">{{ getReservoirName(row.reservoir_id) }}</span>
          <el-tag v-else size="small" type="info" effect="plain">全部水库</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="比较方向" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.compare_direction === 'gt'" type="danger" size="small" effect="dark">超上限</el-tag>
          <el-tag v-else type="primary" size="small" effect="dark">低下限</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="触发等级" width="80" align="center">
        <template #default="{ row }">
          <el-tag
            :type="triggerClassTagType(row.trigger_class)"
            size="small"
            effect="plain"
          >
            {{ row.trigger_class }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="预警级别" width="90" align="center">
        <template #default="{ row }">
          <el-tag
            :type="alertLevelTagType(row.alert_level)"
            size="small"
            effect="dark"
          >
            {{ alertLevelLabel(row.alert_level) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="备注" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.remark || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="70" align="center">
        <template #default="{ row }">
          <el-switch
            :model-value="row.is_active"
            :active-value="1"
            :inactive-value="0"
            :loading="switchLoadingMap[row.id]"
            @change="(val) => handleToggleActive(row, val)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button type="danger" link size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无预警规则" />
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
      v-model="dialogVisible"
      :title="isEditMode ? '编辑预警规则' : '新增预警规则'"
      width="640px"
      :close-on-click-modal="false"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="规则名称" prop="rule_name">
          <el-input v-model="form.rule_name" placeholder="请输入规则名称" maxlength="100" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="关联指标" prop="indicator_id">
              <el-select v-model="form.indicator_id" placeholder="请选择指标" class="w-full">
                <el-option
                  v-for="item in indicatorOptions"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="适用水库" prop="reservoir_id">
              <el-select v-model="form.reservoir_id" placeholder="全部水库(全局规则)" clearable class="w-full">
                <el-option
                  v-for="item in reservoirOptions"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="比较方向" prop="compare_direction">
              <el-select v-model="form.compare_direction" placeholder="请选择" class="w-full">
                <el-option label="超上限告警 (gt)" value="gt" />
                <el-option label="低下限告警 (lt)" value="lt" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="触发等级" prop="trigger_class">
              <el-select v-model="form.trigger_class" placeholder="请选择" class="w-full">
                <el-option label="Ⅰ类" value="I" />
                <el-option label="Ⅱ类" value="II" />
                <el-option label="Ⅲ类" value="III" />
                <el-option label="Ⅳ类" value="IV" />
                <el-option label="Ⅴ类" value="V" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="预警级别" prop="alert_level">
              <el-select v-model="form.alert_level" placeholder="请选择" class="w-full">
                <el-option label="提示 (info)" :value="1" />
                <el-option label="警告 (warning)" :value="2" />
                <el-option label="严重 (critical)" :value="3" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用状态" prop="is_active">
              <el-switch v-model="form.is_active" :active-value="1" :inactive-value="0" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="3"
            placeholder="备注说明（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ isEditMode ? '保 存' : '确 定' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 预警规则管理页
 * 功能描述：预警规则列表查询、筛选、分页、新增、编辑、删除、启用/禁用切换
 * 依赖组件：无
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { getAlertRuleList, getAlertRuleDetail, createAlertRule, updateAlertRule, deleteAlertRule } from '@/api/alert_rules'
import { getIndicatorList } from '@/api/indicator'
import { getReservoirList } from '@/api/reservoir'

const loading = ref(false)
const filterIndicatorId = ref(null)
const filterReservoirId = ref(undefined)
const filterIsActive = ref(null)

const ruleList = ref([])
const indicatorOptions = ref([])
const reservoirOptions = ref([])
const switchLoadingMap = reactive({})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0,
  total_pages: 0
})

const getIndicatorName = (id) => {
  const item = indicatorOptions.value.find((i) => i.id === id)
  return item ? item.name : `ID:${id}`
}

const getReservoirName = (id) => {
  const item = reservoirOptions.value.find((i) => i.id === id)
  return item ? item.name : `ID:${id}`
}

const triggerClassTagType = (cls) => {
  const map = { I: 'success', II: 'success', III: 'warning', IV: 'warning', V: 'danger' }
  return map[cls] || 'info'
}

const alertLevelTagType = (level) => {
  const map = { 1: 'info', 2: 'warning', 3: 'danger' }
  return map[level] || 'info'
}

const alertLevelLabel = (level) => {
  const map = { 1: '提示', 2: '警告', 3: '严重' }
  return map[level] || `Level${level}`
}

const fetchRuleList = async () => {
  loading.value = true
  try {
    const params = {
      indicator_id: filterIndicatorId.value ?? undefined,
      reservoir_id: filterReservoirId.value === -1 ? null : filterReservoirId.value ?? undefined,
      is_active: filterIsActive.value !== null && filterIsActive.value !== undefined ? filterIsActive.value : undefined,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const res = await getAlertRuleList(params)
    ruleList.value = res.data.lists
    pagination.total = res.data.pagination.total
    pagination.total_pages = res.data.pagination.total_pages
  } catch (e) {
    ElMessage.error(e.message || '获取规则列表失败')
    ruleList.value = []
  } finally {
    loading.value = false
  }
}

const fetchOptions = async () => {
  try {
    const [indicatorRes, reservoirRes] = await Promise.all([
      getIndicatorList({ page: 1, page_size: 9999 }),
      getReservoirList({ page: 1, page_size: 100 })
    ])
    indicatorOptions.value = indicatorRes.data.lists || []
    reservoirOptions.value = reservoirRes.data.lists || []
  } catch {
    /* 选项加载失败不影响主表格使用，静默处理 */
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchRuleList()
}

const handlePageChange = () => {
  fetchRuleList()
}

const handleSizeChange = () => {
  pagination.page = 1
  fetchRuleList()
}

onMounted(() => {
  fetchOptions()
  fetchRuleList()
})

const dialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const isEditMode = ref(false)
const editingRuleId = ref(null)

const form = reactive({
  rule_name: '',
  indicator_id: null,
  reservoir_id: null,
  compare_direction: '',
  trigger_class: '',
  alert_level: null,
  is_active: 1,
  remark: ''
})

const formRules = {
  rule_name: [
    { required: true, message: '请输入规则名称', trigger: 'blur' },
    { max: 100, message: '规则名称不超过100个字符', trigger: 'blur' }
  ],
  indicator_id: [
    { required: true, message: '请选择关联指标', trigger: 'change' }
  ],
  compare_direction: [
    { required: true, message: '请选择比较方向', trigger: 'change' }
  ],
  trigger_class: [
    { required: true, message: '请选择触发等级', trigger: 'change' }
  ],
  alert_level: [
    { required: true, message: '请选择预警级别', trigger: 'change' }
  ]
}

const openCreateDialog = () => {
  isEditMode.value = false
  editingRuleId.value = null
  dialogVisible.value = true
}

const openEditDialog = async (row) => {
  isEditMode.value = true
  editingRuleId.value = row.id
  dialogVisible.value = true
  try {
    const res = await getAlertRuleDetail(row.id)
    const detail = res.data
    form.rule_name = detail.rule_name
    form.indicator_id = detail.indicator_id
    form.reservoir_id = detail.reservoir_id ?? null
    form.compare_direction = detail.compare_direction
    form.trigger_class = detail.trigger_class
    form.alert_level = detail.alert_level
    form.is_active = detail.is_active
    form.remark = detail.remark || ''
  } catch (e) {
    ElMessage.error(e.message || '获取规则详情失败')
    dialogVisible.value = false
  }
}

const resetForm = () => {
  isEditMode.value = false
  editingRuleId.value = null
  form.rule_name = ''
  form.indicator_id = null
  form.reservoir_id = null
  form.compare_direction = ''
  form.trigger_class = ''
  form.alert_level = null
  form.is_active = 1
  form.remark = ''
  formRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  submitLoading.value = true
  try {
    const payload = {
      rule_name: form.rule_name,
      indicator_id: form.indicator_id,
      reservoir_id: form.reservoir_id ?? undefined,
      compare_direction: form.compare_direction,
      trigger_class: form.trigger_class,
      alert_level: form.alert_level,
      is_active: form.is_active,
      remark: form.remark || undefined
    }
    if (isEditMode.value) {
      await updateAlertRule(editingRuleId.value, payload)
      ElMessage.success('规则更新成功')
    } else {
      await createAlertRule(payload)
      ElMessage.success('规则创建成功')
    }
    dialogVisible.value = false
    pagination.page = 1
    await fetchRuleList()
  } catch (e) {
    ElMessage.error(e.message || (isEditMode.value ? '更新规则失败' : '创建规则失败'))
  } finally {
    submitLoading.value = false
  }
}

const handleToggleActive = async (row, val) => {
  const newVal = val ? 1 : 0
  if (newVal === row.is_active) return

  switchLoadingMap[row.id] = true
  try {
    await updateAlertRule(row.id, { is_active: newVal })
    ElMessage.success(newVal ? '规则已启用' : '规则已禁用')
    row.is_active = newVal
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    switchLoadingMap[row.id] = false
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除该预警规则吗？删除后不可恢复。', '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  try {
    await deleteAlertRule(id)
    ElMessage.success('规则删除成功')
    await fetchRuleList()
  } catch (e) {
    ElMessage.error(e.message || '删除规则失败')
  }
}
</script>
