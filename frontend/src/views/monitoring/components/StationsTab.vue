<template>
  <el-table
    v-loading="loading"
    :data="stationList"
    border
    stripe
    highlight-current-row
    class="w-full"
  >
    <el-table-column prop="name" label="站点名称" min-width="160" />
    <el-table-column label="站点编码" width="150">
      <template #default="{ row }">
        <span class="font-mono text-xs">{{ row.code }}</span>
      </template>
    </el-table-column>
    <el-table-column label="站点类型" width="120" align="center">
      <template #default="{ row }">
        <el-tag :type="typeTagMap[row.type] || 'info'" size="small">
          {{ typeLabelMap[row.type] || row.type }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="运行状态" width="120" align="center">
      <template #default="{ row }">
        <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
          {{ row.status === 1 ? '在线' : '离线' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="最后数据时间" width="180" align="center">
      <template #default="{ row }">
        <span class="text-gray-500">{{ formatDateTime(row.last_data_time) || '暂无数据' }}</span>
      </template>
    </el-table-column>
    <template #empty>
      <el-empty description="该水库暂无监测站点" />
    </template>
  </el-table>
</template>

<script setup>
/**
 * 监测站点 Tab（已对接真实数据）
 * 功能描述：根据当前水库 ID，调取监测站点列表
 * 依赖组件：无
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getStationList } from '@/api/station'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const reservoirId = computed(() => Number(route.params.id))

const loading = ref(true)
const stationList = ref([])

const typeLabelMap = {
  auto: '自动站',
  manual: '人工站',
  sensing: '遥感站'
}

const typeTagMap = {
  auto: 'success',
  manual: 'warning',
  sensing: 'info'
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await getStationList({
      reservoir_id: reservoirId.value || undefined,
      page: 1,
      page_size: 9999
    })
    stationList.value = res.data?.lists || []
  } catch {
    ElMessage.error('获取站点列表失败')
    stationList.value = []
  } finally {
    loading.value = false
  }
})
</script>
