<template>
  <el-container class="h-screen">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="transition-all duration-300 bg-slate-800 flex flex-col">
      <div class="h-16 flex items-center justify-center border-b border-slate-700">
        <el-icon class="text-slate-300 text-2xl" :size="24"><Monitor /></el-icon>
        <span v-show="!isCollapse" class="ml-2 text-white font-semibold text-base whitespace-nowrap">水库监测平台</span>
      </div>

      <el-scrollbar class="flex-1">
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :collapse-transition="false"
          background-color="#1e293b"
          text-color="#94a3b8"
          active-text-color="#ffffff"
          router
          class="border-r-0"
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-sub-menu index="monitoring">
            <template #title>
              <el-icon><DataLine /></el-icon>
              <span>监测管理</span>
            </template>
            <el-menu-item index="/alerts/list">
              <el-icon><WarningFilled /></el-icon>
              <span>预警中心</span>
            </el-menu-item>
            <el-menu-item index="/monitoring/records">
              <el-icon><Document /></el-icon>
              <span>监测数据记录</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="rag">
            <template #title>
              <el-icon><ChatLineSquare /></el-icon>
              <span>智能问答</span>
            </template>
            <el-menu-item index="/rag/knowledge">
              <el-icon><Document /></el-icon>
              <span>知识库管理</span>
            </el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="system">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </template>
            <el-menu-item index="/system/users">
              <el-icon><User /></el-icon>
              <span>用户与权限管理</span>
            </el-menu-item>
            <el-menu-item index="/system/reservoirs">
              <el-icon><Collection /></el-icon>
              <span>水库站点配置管理</span>
            </el-menu-item>
            <el-menu-item index="/system/alert-rules">
              <el-icon><WarningFilled /></el-icon>
              <span>预警规则管理</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container>
      <el-header class="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-4">
        <div class="flex items-center gap-3">
          <el-button
            text
            @click="isCollapse = !isCollapse"
            class="!text-gray-500 hover:!text-gray-700"
          >
            <el-icon :size="20">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
          </el-button>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentPageName">{{ currentPageName }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <el-dropdown trigger="click">
          <div class="flex items-center gap-2 cursor-pointer">
            <el-avatar :size="32" class="!bg-teal-500">
              <span class="text-white text-sm">{{ userInitial }}</span>
            </el-avatar>
            <span class="text-sm text-gray-700">{{ username }}</span>
            <el-icon class="text-gray-400"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>
                <el-icon><User /></el-icon>
                {{ username }}
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="bg-gray-50 p-6">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
/**
 * 主布局组件
 * 功能描述：侧边栏 + 顶部栏 + 内容区的主页面框架
 * 依赖组件：无
 */
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAlertWebSocket } from '@/composables/useAlertWebSocket'
import {
  Monitor,
  Setting,
  User,
  Collection,
  DataLine,
  Document,
  Fold,
  Expand,
  ArrowDown,
  SwitchButton,
  House,
  WarningFilled,
  ChatLineSquare
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

useAlertWebSocket()

const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

const username = computed(() => authStore.userInfo?.username || '用户')

const userInitial = computed(() => {
  const name = username.value
  return name ? name.charAt(0).toUpperCase() : 'U'
})

const currentPageName = computed(() => {
  const name = route.meta?.title
  return typeof name === 'string' ? name : ''
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>