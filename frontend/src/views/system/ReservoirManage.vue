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
        <el-select
          v-model="filterStatus"
          placeholder="状态"
          clearable
          class="w-28"
        >
          <el-option label="启用" :value="1" />
          <el-option label="停用" :value="0" />
        </el-select>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
      <el-button type="primary">
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
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-switch
            :model-value="row.status === 1"
            disabled
            size="small"
          />
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="70" align="center" />
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
import { getReservoirList } from '@/api/reservoir'

const loading = ref(false)
const searchKeyword = ref('')
const filterWatershed = ref(null)
const filterWaterGrade = ref(null)
const filterStatus = ref(null)

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
      status: filterStatus.value ?? undefined,
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
</script>
