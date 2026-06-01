<template>
  <el-table
    :data="skeletonData"
    border
    stripe
    highlight-current-row
    class="w-full"
    @row-click="handleRowClick"
  >
    <el-table-column prop="name" label="站点名称" min-width="160">
      <template #default>
        <el-skeleton :loading="true" animated style="width: 70%">
          <template #template>
            <el-skeleton-item variant="text" style="height: 14px" />
          </template>
        </el-skeleton>
      </template>
    </el-table-column>
    <el-table-column label="站点类型" width="120" align="center">
      <template #default>
        <el-skeleton :loading="true" animated style="width: 60%; margin: 0 auto">
          <template #template>
            <el-skeleton-item variant="text" style="height: 18px; border-radius: 9px" />
          </template>
        </el-skeleton>
      </template>
    </el-table-column>
    <el-table-column label="运行状态" width="120" align="center">
      <template #default>
        <el-skeleton :loading="true" animated style="width: 60%; margin: 0 auto">
          <template #template>
            <el-skeleton-item variant="text" style="height: 18px; border-radius: 9px" />
          </template>
        </el-skeleton>
      </template>
    </el-table-column>
    <el-table-column label="最后数据时间" width="180" align="center">
      <template #default>
        <el-skeleton :loading="true" animated style="width: 80%; margin: 0 auto">
          <template #template>
            <el-skeleton-item variant="text" style="height: 14px" />
          </template>
        </el-skeleton>
      </template>
    </el-table-column>
    <template #empty>
      <el-empty description="该水库暂无监测站点" />
    </template>
  </el-table>
</template>

<script setup>
/**
 * 监测站点 Tab
 * 功能描述：站点列表表格，行内容用 el-skeleton 占位
 * 依赖组件：无
 */
import { ElMessage } from 'element-plus'

const skeletonData = Array.from({ length: 6 }, (_, i) => ({ id: i }))

const handleRowClick = () => {
  ElMessage.info('该功能开发中')
}
</script>
