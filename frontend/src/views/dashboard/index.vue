<template>
  <section class="space-y-4">
    <el-breadcrumb separator="/" class="text-sm">
      <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>告警总览</el-breadcrumb-item>
    </el-breadcrumb>

    <header class="flex items-center justify-between">
      <h1 class="text-xl font-semibold text-gray-900">告警总览</h1>
      <span class="text-xs text-gray-500">下次刷新倒计时 {{ countdown }}s</span>
    </header>

    <section class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <el-card shadow="never" :body-style="{ padding: '16px' }">
        <el-statistic title="水库总数" :value="overview?.reservoir_count ?? 0">
          <template #prefix>
            <el-icon class="text-teal-500"><Histogram /></el-icon>
          </template>
        </el-statistic>
      </el-card>

      <el-card shadow="never" :body-style="{ padding: '16px' }">
        <el-statistic title="水质正常数" :value="overview?.normal_count ?? 0" :value-style="{ color: '#10b981' }">
          <template #prefix>
            <el-icon class="text-emerald-500"><CircleCheckFilled /></el-icon>
          </template>
        </el-statistic>
      </el-card>

      <el-card shadow="never" :body-style="{ padding: '16px' }">
        <el-statistic
          title="异常记录数"
          :value="overview?.record_alert_count ?? 0"
          :value-style="{ color: '#e6a23c' }"
        >
          <template #prefix>
            <el-icon class="text-orange-500"><WarningFilled /></el-icon>
          </template>
        </el-statistic>
      </el-card>

      <el-card shadow="never" :body-style="{ padding: '16px' }">
        <el-statistic title="规则预警" :value="overview?.rule_alert_count ?? 0" :value-style="{ color: '#409eff' }">
          <template #prefix>
            <el-icon class="text-blue-500"><InfoFilled /></el-icon>
          </template>
        </el-statistic>
      </el-card>

      <el-card shadow="never" :body-style="{ padding: '16px' }">
        <el-statistic title="AI趋势预警" :value="overview?.ai_alert_count ?? 0" :value-style="{ color: '#e6a23c' }">
          <template #prefix>
            <el-icon class="text-orange-500"><DataAnalysis /></el-icon>
          </template>
        </el-statistic>
      </el-card>

      <el-card shadow="never" :body-style="{ padding: '16px' }">
        <el-statistic
          title="离线站点数"
          :value="overview?.offline_stations ?? 0"
          :value-style="{ color: offlineCountColor }"
        >
          <template #prefix>
            <el-icon :class="offlineCount === 0 ? 'text-emerald-500' : 'text-amber-500'"><CircleCloseFilled /></el-icon>
          </template>
        </el-statistic>
      </el-card>
    </section>

    <main class="grid grid-cols-1 lg:grid-cols-5 gap-4">
      <section class="lg:col-span-3 space-y-3">
        <header class="flex items-center justify-between">
          <h2 class="text-base font-semibold text-gray-900">水库健康状况</h2>
          <el-button v-if="reservoirsError" size="small" type="primary" @click="loadAll">重新加载</el-button>
        </header>

        <el-skeleton v-if="reservoirsLoading" :rows="6" animated />
        <el-empty v-else-if="reservoirsError" description="数据加载失败" />
        <el-empty v-else-if="!reservoirs.length" description="暂无数据" />
        <div
          v-else
          class="grid grid-cols-1 min-[768px]:grid-cols-2 min-[1400px]:grid-cols-3 gap-3"
        >
          <el-card
            v-for="r in reservoirs"
            :key="r.id"
            shadow="hover"
            class="cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
            :body-style="{ padding: '14px' }"
            @click="goReservoir(r.id)"
          >
            <header class="flex items-center justify-between mb-2">
              <span class="text-sm font-semibold text-gray-900 truncate">{{ r.name }}</span>
              <el-badge
                v-if="r.alert_count > 0"
                :value="r.alert_count"
                type="danger"
              />
            </header>
            <el-tag
              :type="waterGradeTagType(r.water_grade)"
              size="small"
              effect="light"
              class="mb-2"
            >
              {{ r.water_grade || '暂无数据' }}
            </el-tag>
            <ul class="grid gap-1 text-xs text-gray-500" :class="indicatorGridClass(r.indicators)">
              <li v-for="ind in r.indicators" :key="ind.code">
                <span>{{ ind.name }}</span>
                <p class="text-sm font-medium text-gray-900 mt-0.5">
                  {{ formatIndicator(ind.value, ind.unit) }}
                </p>
              </li>
            </ul>
          </el-card>
        </div>
      </section>

      <aside class="lg:col-span-2 space-y-3">
        <header class="flex items-center justify-between">
          <h2 class="text-base font-semibold text-gray-900">最新告警</h2>
          <el-button v-if="alertsError" size="small" type="primary" @click="loadAll">重新加载</el-button>
          <span v-else class="text-xs text-gray-400">仅展示最新 {{ ALERT_LIMIT }} 条</span>
        </header>

        <el-skeleton v-if="alertsLoading" :rows="4" animated />
        <el-empty v-else-if="alertsError" description="数据加载失败" />
        <el-empty v-else-if="!alerts.length" description="暂无活跃告警" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="a in alerts"
            :key="a.alert_id"
            :type="alertLevelTagType(a.alert_level)"
            :timestamp="formatRelativeTime(a.detected_at)"
            placement="top"
          >
            <div>
              <el-tag
                :type="alertLevelTagType(a.alert_level)"
                size="small"
                effect="light"
                class="mr-2"
              >
                {{ alertLevelLabel(a.alert_level) }}
              </el-tag>
              <el-tag v-if="a.source === 1" type="warning" size="small">AI趋势</el-tag>
              <el-tag v-else-if="a.source === 0" type="info" size="small">规则</el-tag>
              <span class="text-sm text-gray-900">{{ a.title }}</span>
              <p
                v-if="a.indicators && a.indicators.length"
                class="text-xs text-gray-500 mt-1"
              >
                <span
                  v-for="(ind, idx) in a.indicators"
                  :key="idx"
                >
                  <span v-if="idx > 0" class="mx-1">·</span>
                  {{ ind.name }} {{ ind.value }}{{ ind.limit ? `/${ind.limit}` : '' }}
                </span>
              </p>
            </div>
          </el-timeline-item>
        </el-timeline>
      </aside>
    </main>
  </section>
</template>

<script setup>
/**
 * 首页告警总览
 * 功能描述：指挥驾驶舱。展示统计概览（4 个统计卡片）、水库健康卡片（占位）、最新告警时间线（占位），5 分钟自动刷新。
 * 依赖组件：无
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Histogram,
  CircleCheckFilled,
  WarningFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'
import { getDashboardOverview, getReservoirOverviewList, getLatestAlerts } from '@/api/dashboard'

const REFRESH_INTERVAL = 300
const ALERT_LIMIT = 5

const WATER_GRADE_TAG_TYPE = {
  'Ⅰ类': 'primary',
  'Ⅱ类': 'success',
  'Ⅲ类': 'warning',
  'Ⅳ类': 'danger',
  'Ⅴ类': 'danger',
  '劣Ⅴ类': 'danger'
}
const ALERT_LEVEL_TAG = { 1: 'info', 2: 'warning', 3: 'danger' }

const ALERT_LEVEL_LABEL = { 1: '提示', 2: '预警', 3: '告警' }
const router = useRouter()

const overview = ref(null)
const overviewLoading = ref(true)
const overviewError = ref(false)

const reservoirs = ref([])
const reservoirsLoading = ref(true)
const reservoirsError = ref(false)

const alerts = ref([])
const alertsLoading = ref(true)
const alertsError = ref(false)

const countdown = ref(REFRESH_INTERVAL)
let refreshTimer = null
let tickTimer = null
let isFirstLoad = true

const offlineCount = computed(() => overview.value?.offline_stations ?? 0)
const offlineCountColor = computed(() => (offlineCount.value === 0 ? '#10b981' : '#f59e0b'))

const waterGradeTagType = (grade) => WATER_GRADE_TAG_TYPE[grade] || 'info'
const alertLevelTagType = (level) => ALERT_LEVEL_TAG[level] ?? ALERT_LEVEL_TAG[Number(level)] ?? 'info'
const alertLevelLabel = (level) => ALERT_LEVEL_LABEL[level] ?? ALERT_LEVEL_LABEL[Number(level)] ?? '告警'

const indicatorGridClass = (indicators) => {
  if (!indicators?.length) return 'grid-cols-1'
  if (indicators.length <= 3) return 'grid-cols-3'
  if (indicators.length <= 4) return 'grid-cols-4'
  return 'grid-cols-3'
}

const formatIndicator = (value, unit) => {
  if (value === null || value === undefined || value === '') return '--'
  return `${value}${unit || ''}`
}

const formatRelativeTime = (target) => {
  if (!target) return ''
  const t = new Date(target).getTime()
  if (isNaN(t)) return ''
  const diff = Math.floor((Date.now() - t) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 604800) return `${Math.floor(diff / 86400)}天前`
  const d = new Date(t)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const goReservoir = (id) => {
  if (!id) return
  router.push(`/monitoring/reservoirs/${id}`)
}

/**
 * 并发拉取三个区域数据，allSettled 保证互不阻塞
 */
const loadAll = async () => {
  if (isFirstLoad) {
    overviewLoading.value = true
  }
  overviewError.value = false
  reservoirsLoading.value = true
  reservoirsError.value = false
  alertsLoading.value = true
  alertsError.value = false

  const [r1, r2, r3] = await Promise.allSettled([
    getDashboardOverview(),
    getReservoirOverviewList(),
    getLatestAlerts(),
  ])

  if (r1.status === 'fulfilled') {
    overview.value = r1.value.data || null
  } else {
    overviewError.value = true
  }

  if (r2.status === 'fulfilled') {
    reservoirs.value = r2.value.data || []
  } else {
    reservoirsError.value = true
  }

  if (r3.status === 'fulfilled') {
    alerts.value = r3.value.data || []
  } else {
    alertsError.value = true
  }

  overviewLoading.value = false
  reservoirsLoading.value = false
  alertsLoading.value = false

  isFirstLoad = false
  countdown.value = REFRESH_INTERVAL
}

const startTimers = () => {
  refreshTimer = setInterval(loadAll, REFRESH_INTERVAL * 1000)
  tickTimer = setInterval(() => {
    if (countdown.value > 0) countdown.value -= 1
  }, 1000)
}

const stopTimers = () => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (tickTimer) clearInterval(tickTimer)
  refreshTimer = null
  tickTimer = null
}

onMounted(() => {
  loadAll()
  startTimers()
})

onUnmounted(stopTimers)
</script>
