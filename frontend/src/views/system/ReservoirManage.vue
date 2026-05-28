<template>
  <div>
    <el-tabs v-model="activeTab" class="mb-4">
      <el-tab-pane label="水库管理" name="reservoir">
        <reservoir-tab v-if="activeTab === 'reservoir'" />
      </el-tab-pane>
      <el-tab-pane label="监测站点管理" name="station">
        <station-tab v-if="activeTab === 'station'" />
      </el-tab-pane>
      <el-tab-pane label="监测指标管理" name="indicator">
        <indicator-tab v-if="activeTab === 'indicator'" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
/**
 * 系统配置管理页
 * 功能描述：水库管理、监测站点管理、监测指标管理三Tab统一页面
 * 依赖组件：ReservoirTab, StationTab, IndicatorTab
 */
import { ref } from 'vue'
import ReservoirTab from './components/ReservoirTab.vue'
import StationTab from './components/StationTab.vue'
import IndicatorTab from './components/IndicatorTab.vue'

const activeTab = ref('reservoir')
</script>
