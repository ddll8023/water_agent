import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    component: () => import('@/views/layout/MainLayout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'system/users',
        name: 'UserManage',
        component: () => import('@/views/system/UserManage.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'system/reservoirs',
        name: 'ReservoirManage',
        component: () => import('@/views/system/ReservoirManage.vue'),
        meta: { title: '水库站点配置管理' }
      },
      {
        path: 'system/alert-rules',
        name: 'AlertRules',
        component: () => import('@/views/system/AlertRules.vue'),
        meta: { title: '预警规则管理' }
      },
      {
        path: 'alerts/list',
        name: 'AlertCenter',
        component: () => import('@/views/alert/AlertCenter.vue'),
        meta: { title: '预警中心' }
      },
      {
        path: 'alerts/:id',
        name: 'AlertDetail',
        component: () => import('@/views/alert/AlertDetail.vue'),
        meta: { title: '预警详情' }
      },
      {
        path: 'monitoring/records',
        name: 'MonitoringRecords',
        component: () => import('@/views/monitoring/MonitoringRecords.vue'),
        meta: { title: '监测数据记录' }
      },
      {
        path: 'monitoring/reservoirs/:id',
        name: 'ReservoirMonitoringDetail',
        component: () => import('@/views/monitoring/ReservoirMonitoringDetail.vue'),
        meta: { title: '实时监测' }
      },
      {
        path: 'rag/knowledge',
        name: 'KnowledgeBase',
        component: () => import('@/views/rag/KnowledgeBase.vue'),
        meta: { title: '知识库管理' }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { requiresAuth: false }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && authStore.isLoggedIn) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router