<template>
  <div>
    <!-- 加载中 -->
    <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <el-card v-for="i in 9" :key="i" shadow="hover">
        <el-skeleton :loading="true" animated>
          <template #template>
            <div class="flex flex-col gap-3">
              <div class="flex items-center justify-between">
                <el-skeleton-item variant="text" style="width: 40px; height: 14px" />
                <el-skeleton-item variant="text" style="width: 50px; height: 18px; border-radius: 9px" />
              </div>
              <el-skeleton-item variant="h1" style="width: 60%; height: 28px" />
              <el-skeleton-item variant="text" style="width: 80%; height: 14px" />
            </div>
          </template>
        </el-skeleton>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="!cardList.length" description="暂无实时监测数据" />

    <!-- 数据卡片 -->
    <el-row v-else :gutter="20">
      <el-col
        v-for="item in cardList"
        :key="item.indicatorId"
        :xs="24"
        :sm="12"
        :md="8"
        class="mb-5"
      >
        <el-card shadow="hover" class="h-full">
          <div class="flex flex-col">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-gray-500">{{ item.indicatorName }}</span>
              <el-tag size="small" effect="plain" type="info">{{ item.indicatorCode }}</el-tag>
            </div>

            <div class="flex items-baseline gap-1 my-1 h-9">
              <span class="text-2xl font-semibold text-gray-800 font-mono">
                {{ item.value }}
              </span>
              <span v-if="item.unit" class="text-sm text-gray-400">({{ item.unit }})</span>
            </div>

            <div class="flex items-center justify-between text-xs text-gray-400 mt-2">
              <span>标准限值</span>
              <span>{{ item.standardLimit ?? '-' }}</span>
            </div>

            <div class="flex items-center justify-between text-xs text-gray-400 mt-1">
              <span />
              <span>{{ formatDateTime(item.recordTime) }}</span>
            </div>

            <el-divider class="!my-3" />

            <div class="flex justify-end">
              <el-link type="primary" :underline="false" @click="handleViewTrend(item)">
                <el-icon class="mr-1"><DataAnalysis /></el-icon>
                查看趋势
              </el-link>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <indicator-trend-dialog
      v-model="dialogVisible"
      :indicator-name="activeIndicator?.indicatorName || ''"
      :standard-limit="activeIndicator?.standardLimit ?? null"
      :reservoir-id="reservoirId"
      :indicator-id="activeIndicator?.indicatorId ?? undefined"
    />
  </div>
</template>

<script setup>
/**
 * 实时数据 Tab
 * 功能描述：根据当前水库 ID，获取各指标最新监测值并呈现为指标卡片网格
 * 依赖组件：IndicatorTrendDialog
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { DataAnalysis } from '@element-plus/icons-vue'
import { getReservoirLatestIndicators } from '@/api/monitoring'
import { getIndicatorList } from '@/api/indicator'
import IndicatorTrendDialog from './IndicatorTrendDialog.vue'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const reservoirId = computed(() => Number(route.params.id))

const loading = ref(true)
const cardList = ref([])
const dialogVisible = ref(false)
const activeIndicator = ref(null)

/** 获取所有指标元数据（编码、单位、标准限值） */
const fetchIndicators = async () => {
  const res = await getIndicatorList({ page: 1, page_size: 9999 })
  return res.data?.lists || []
}

/** 取指标的标准限值（取五类限值中的最大值） */
const _getLimit = (indicator) => {
  const limits = [
    indicator.standard_limit_i,
    indicator.standard_limit_ii,
    indicator.standard_limit_iii,
    indicator.standard_limit_iv,
    indicator.standard_limit_v
  ].filter((v) => v !== null && v !== undefined)
  return limits.length ? Math.max(...limits) : null
}

onMounted(async () => {
  loading.value = true
  try {
    const [recordsData, indicators] = await Promise.all([
      getReservoirLatestIndicators({ reservoir_id: reservoirId.value }),
      fetchIndicators()
    ])

    const records = recordsData?.data?.records || []
    if (!records.length) {
      cardList.value = []
      return
    }

    const indicatorMap = new Map(indicators.map((i) => [i.id, i]))

    cardList.value = records.map((record) => {
      const indicator = indicatorMap.get(record.indicator_id) || {}
      return {
        indicatorId: record.indicator_id,
        indicatorName: record.indicator_name,
        indicatorCode: indicator.code || '',
        unit: indicator.unit || '',
        value: record.value ?? '-',
        recordTime: record.record_time || '',
        qualityFlag: record.quality_flag,
        standardLimit: _getLimit(indicator)
      }
    })
  } catch (e) {
    ElMessage.error('获取实时监测数据失败')
    cardList.value = []
  } finally {
    loading.value = false
  }
})

const handleViewTrend = (item) => {
  activeIndicator.value = item
  dialogVisible.value = true
}
</script>
