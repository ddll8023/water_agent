<template>
  <div>
    <el-tabs v-model="activeTab" type="border-card" class="bg-white rounded-lg shadow-sm">
      <el-tab-pane label="用户管理" name="users">
        <div class="flex items-center justify-between mb-4">
          <el-button type="primary" disabled @click="handleAddUser">
            <el-icon><Plus /></el-icon>
            新增用户
          </el-button>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用户名、真实姓名、手机号"
            clearable
            class="w-72"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <el-table
          v-loading="loading"
          :data="userList"
          border
          stripe
          class="w-full"
          empty-text="暂无用户数据"
        >
          <el-table-column prop="username" label="用户名" min-width="120" />
          <el-table-column prop="real_name" label="真实姓名" min-width="100">
            <template #default="{ row }">
              {{ row.real_name || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="所属角色" width="100">
            <template #default="{ row }">
              <el-tag :type="getRoleTagType(row.role_id)" size="small">
                {{ getRoleName(row.role_id) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="手机号" min-width="130">
            <template #default="{ row }">
              {{ row.phone || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="dingtalk_id" label="钉钉ID" min-width="140">
            <template #default="{ row }">
              {{ row.dingtalk_id || '-' }}
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
          <el-table-column label="最后登录时间" min-width="170">
            <template #default="{ row }">
              {{ formatDateTime(row.last_login) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="240" fixed="right">
            <template #default>
              <el-tooltip content="功能开发中，敬请期待" placement="top">
                <el-button type="primary" link disabled>编辑</el-button>
              </el-tooltip>
              <el-tooltip content="功能开发中，敬请期待" placement="top">
                <el-button type="warning" link disabled>重置密码</el-button>
              </el-tooltip>
              <el-tooltip content="功能开发中，敬请期待" placement="top">
                <el-button type="danger" link disabled>禁用</el-button>
              </el-tooltip>
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
      </el-tab-pane>

      <el-tab-pane label="角色管理" name="roles">
        <el-empty description="功能开发中，敬请期待" :image-size="120" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
/**
 * 用户管理页
 * 功能描述：系统管理 - 用户管理（已对接用户列表），角色管理（开发中）
 * 依赖组件：无
 */
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { getUserList } from '@/api/user'

const activeTab = ref('users')
const loading = ref(false)
const searchKeyword = ref('')

const userList = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0,
  total_pages: 0
})

const roleMap = {
  1: { name: '管理员', type: '' },
  2: { name: '监测员', type: 'success' },
  3: { name: '分析员', type: 'warning' }
}

const getRoleName = (roleId) => {
  return roleMap[roleId]?.name || `角色${roleId}`
}

const getRoleTagType = (roleId) => {
  return roleMap[roleId]?.type || 'info'
}

const formatDateTime = (value) => {
  if (!value) return '-'
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const fetchUserList = async () => {
  loading.value = true
  try {
    const res = await getUserList({
      keyword: searchKeyword.value || null,
      role_id: null,
      status: null,
      page: pagination.page,
      page_size: pagination.page_size
    })
    userList.value = res.data.lists
    pagination.total = res.data.pagination.total
    pagination.total_pages = res.data.pagination.total_pages
  } catch (e) {
    ElMessage.error(e.message || '获取用户列表失败')
    userList.value = []
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchUserList()
}

const handlePageChange = () => {
  fetchUserList()
}

const handleSizeChange = () => {
  pagination.page = 1
  fetchUserList()
}

const handleAddUser = () => {
  ElMessage.info('功能开发中，敬请期待')
}

onMounted(() => {
  fetchUserList()
})
</script>