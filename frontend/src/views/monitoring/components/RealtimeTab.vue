<template>
  <div>
    <el-row :gutter="20">
      <el-col
        v-for="item in indicators"
        :key="item.id"
        :xs="24"
        :sm="12"
        :md="8"
        class="mb-5"
      >
        <el-card shadow="hover" class="h-full">
          <div class="flex flex-col">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-gray-500">{{ item.name }}</span>
              <el-tag size="small" effect="plain" type="info">{{ item.code }}</el-tag>
            </div>

            <div class="flex items-baseline gap-1 my-1 h-9">
              <el-skeleton :loading="true" animated class="flex-1">
                <template #template>
                  <el-skeleton-item variant="h1" style="width: 60%" />
                </template>
              </el-skeleton>
            </div>

            <div class="flex items-center justify-between text-xs text-gray-400 mt-2">
              <span>限值</span>
              <el-skeleton :loading="true" animated style="width: 50%">
                <template #template>
                  <el-skeleton-item variant="text" style="width: 100%" />
                </template>
              </el-skeleton>
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
      :indicator-name="activeIndicator?.name || ''"
      :standard-limit="activeIndicator?.standardLimit ?? null"
    />
  </div>
</template>

<script setup>
/**
 * 实时数据 Tab
 * 功能描述：9 张指标卡片网格（3×3），数值与限值用 el-skeleton 占位
 * 依赖组件：IndicatorTrendDialog
 */
import { ref } from 'vue'
import { DataAnalysis } from '@element-plus/icons-vue'
import { INDICATOR_LIST } from '../mock'
import IndicatorTrendDialog from './IndicatorTrendDialog.vue'

const indicators = INDICATOR_LIST

const dialogVisible = ref(false)
const activeIndicator = ref(null)

const handleViewTrend = (item) => {
  activeIndicator.value = item
  dialogVisible.value = true
}
</script>
