<template>
  <div>
    <el-tabs v-model="activeTab" type="border-card" class="bg-white rounded-lg shadow-sm">
      <el-tab-pane label="用户管理" name="users">
        <div class="flex items-center justify-between mb-4">
          <el-button type="primary" @click="handleAddUser">
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
            <template #default="{ row }">
              <el-button type="primary" link @click="handleEditUser(row)">编辑</el-button>
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
        <el-table
          v-loading="roleLoading"
          :data="roleList"
          border
          stripe
          class="w-full"
          empty-text="暂无角色数据"
        >
          <el-table-column prop="id" label="角色ID" width="80" align="center" />
          <el-table-column prop="role_name" label="角色名称" min-width="160">
            <template #default="{ row }">
              <el-tag :type="getRoleTagTypeByName(row.role_name)" size="small">
                {{ row.role_name }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" min-width="170">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default>
              <el-tooltip content="功能开发中，敬请期待" placement="top">
                <el-button type="primary" link disabled>编辑</el-button>
              </el-tooltip>
              <el-tooltip content="功能开发中，敬请期待" placement="top">
                <el-button type="danger" link disabled>删除</el-button>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>

        <div class="flex justify-end mt-4">
          <el-pagination
            v-model:current-page="rolePagination.page"
            v-model:page-size="rolePagination.page_size"
            :total="rolePagination.total"
            :page-sizes="[10, 15, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @size-change="handleRoleSizeChange"
            @current-change="handleRolePageChange"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="addUserDialogVisible"
      title="新增用户"
      width="520px"
      :close-on-click-modal="false"
      @closed="addUserFormRef?.resetFields()"
    >
      <el-form
        ref="addUserFormRef"
        :model="addUserForm"
        :rules="addUserRules"
        label-width="90px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="addUserForm.username"
            placeholder="请输入用户名"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="addUserForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
            maxlength="20"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input
            v-model="addUserForm.real_name"
            placeholder="请输入真实姓名（选填）"
            maxlength="30"
          />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="addUserForm.phone"
            placeholder="请输入手机号（选填）"
            maxlength="11"
          />
        </el-form-item>
        <el-form-item label="所属角色" prop="role_id">
          <el-select
            v-model="addUserForm.role_id"
            placeholder="请选择所属角色"
            class="w-full"
          >
            <el-option
              v-for="role in allRoles"
              :key="role.id"
              :label="role.role_name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="钉钉ID" prop="dingtalk_id">
          <el-input
            v-model="addUserForm.dingtalk_id"
            placeholder="请输入钉钉ID（选填）"
            maxlength="50"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addUserDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addUserLoading" @click="submitAddUser">
          确认添加
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="editDialogVisible"
      title="编辑用户"
      width="520px"
      :close-on-click-modal="false"
      @closed="editUserFormRef?.resetFields()"
    >
      <el-form
        ref="editUserFormRef"
        :model="editUserForm"
        :rules="editUserRules"
        label-width="90px"
      >
        <el-form-item label="用户名">
          <el-input :model-value="editUserForm.username" disabled />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input
            v-model="editUserForm.real_name"
            placeholder="请输入真实姓名（选填）"
            maxlength="30"
          />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="editUserForm.phone"
            placeholder="请输入手机号（选填）"
            maxlength="11"
          />
        </el-form-item>
        <el-form-item label="所属角色" prop="role_id">
          <el-select
            v-model="editUserForm.role_id"
            placeholder="请选择所属角色"
            class="w-full"
          >
            <el-option
              v-for="role in allRoles"
              :key="role.id"
              :label="role.role_name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="钉钉ID" prop="dingtalk_id">
          <el-input
            v-model="editUserForm.dingtalk_id"
            placeholder="请输入钉钉ID（选填）"
            maxlength="50"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch
            v-model="editUserForm.status"
            :active-value="1"
            :inactive-value="0"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editUserLoading" @click="submitEditUser">
          确认保存
        </el-button>
      </template>
    </el-dialog>
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
import { getUserList, addUser, getUserDetail, updateUser } from '@/api/user'
import { getRoleList } from '@/api/role'

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

const roleLoading = ref(false)
const roleList = ref([])
const rolePagination = reactive({
  page: 1,
  page_size: 10,
  total: 0,
  total_pages: 0
})

const addUserDialogVisible = ref(false)
const addUserLoading = ref(false)
const addUserFormRef = ref(null)
const addUserForm = reactive({
  username: '',
  password: '123456',
  real_name: '',
  phone: '',
  role_id: null,
  dingtalk_id: ''
})
const addUserRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  role_id: [
    { required: true, message: '请选择所属角色', trigger: 'change' }
  ]
}
const allRoles = ref([])

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

const getRoleTagTypeByName = (roleName) => {
  const typeMap = {
    '管理员': '',
    '监测员': 'success',
    '分析员': 'warning'
  }
  return typeMap[roleName] || 'info'
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

const fetchAllRoles = async () => {
  try {
    const res = await getRoleList({ page: 1, page_size: 100 })
    allRoles.value = res.data.lists
  } catch {
    allRoles.value = []
  }
}

const handleAddUser = () => {
  addUserForm.username = ''
  addUserForm.password = '123456'
  addUserForm.real_name = ''
  addUserForm.phone = ''
  addUserForm.role_id = null
  addUserForm.dingtalk_id = ''
  addUserFormRef.value?.resetFields()
  addUserDialogVisible.value = true
  fetchAllRoles()
}

const submitAddUser = async () => {
  const valid = await addUserFormRef.value.validate().catch(() => false)
  if (!valid) return

  addUserLoading.value = true
  try {
    await addUser({
      username: addUserForm.username,
      password: addUserForm.password,
      real_name: addUserForm.real_name || null,
      phone: addUserForm.phone || null,
      role_id: addUserForm.role_id,
      dingtalk_id: addUserForm.dingtalk_id || null
    })
    ElMessage.success('添加用户成功')
    addUserDialogVisible.value = false
    await fetchUserList()
  } catch (e) {
    ElMessage.error(e.message || '添加用户失败')
  } finally {
    addUserLoading.value = false
  }
}

const editDialogVisible = ref(false)
const editUserLoading = ref(false)
const editUserFormRef = ref(null)
const editingUserId = ref(null)
const editUserForm = reactive({
  username: '',
  real_name: '',
  phone: '',
  role_id: null,
  dingtalk_id: '',
  status: 1
})
const editUserRules = {
  role_id: [
    { required: true, message: '请选择所属角色', trigger: 'change' }
  ]
}

const handleEditUser = async (row) => {
  editingUserId.value = row.id
  editUserForm.username = row.username
  editUserForm.real_name = ''
  editUserForm.phone = ''
  editUserForm.role_id = null
  editUserForm.dingtalk_id = ''
  editUserForm.status = 1
  editDialogVisible.value = true
  editUserLoading.value = true
  fetchAllRoles()
  try {
    const res = await getUserDetail(row.id)
    editUserForm.username = res.data.username
    editUserForm.real_name = res.data.real_name || ''
    editUserForm.phone = res.data.phone || ''
    editUserForm.role_id = res.data.role_id
    editUserForm.dingtalk_id = res.data.dingtalk_id || ''
    editUserForm.status = res.data.status
  } catch (e) {
    ElMessage.error(e.message || '获取用户详情失败')
    editDialogVisible.value = false
  } finally {
    editUserLoading.value = false
  }
}

const submitEditUser = async () => {
  const valid = await editUserFormRef.value.validate().catch(() => false)
  if (!valid) return

  editUserLoading.value = true
  try {
    await updateUser(editingUserId.value, {
      real_name: editUserForm.real_name || null,
      phone: editUserForm.phone || null,
      role_id: editUserForm.role_id,
      dingtalk_id: editUserForm.dingtalk_id || null,
      status: editUserForm.status
    })
    ElMessage.success('更新用户成功')
    editDialogVisible.value = false
    await fetchUserList()
  } catch (e) {
    ElMessage.error(e.message || '更新用户失败')
  } finally {
    editUserLoading.value = false
  }
}

const fetchRoleList = async () => {
  roleLoading.value = true
  try {
    const res = await getRoleList({
      page: rolePagination.page,
      page_size: rolePagination.page_size
    })
    roleList.value = res.data.lists
    rolePagination.total = res.data.pagination.total
    rolePagination.total_pages = res.data.pagination.total_pages
  } catch (e) {
    ElMessage.error(e.message || '获取角色列表失败')
    roleList.value = []
  } finally {
    roleLoading.value = false
  }
}

const handleRoleSizeChange = () => {
  rolePagination.page = 1
  fetchRoleList()
}

const handleRolePageChange = () => {
  fetchRoleList()
}

watch(activeTab, (newVal) => {
  if (newVal === 'roles') {
    fetchRoleList()
  }
})

onMounted(() => {
  fetchUserList()
})
</script>