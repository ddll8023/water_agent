<template>
  <div class="p-6">
    <header class="mb-6">
      <h1 class="text-xl font-semibold text-gray-900">知识库管理</h1>
      <p class="text-sm text-gray-500 mt-1">上传和管理标准规范、历史案例与应急处置预案</p>
    </header>

    <!-- 筛选栏 -->
    <section class="bg-white rounded-lg shadow-sm p-4 mb-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <el-select v-model="filters.docType" placeholder="文档类型" clearable class="w-32">
          <el-option label="全部" value="" />
          <el-option label="标准规范" :value="0" />
          <el-option label="历史案例" :value="1" />
          <el-option label="处置预案" :value="2" />
          <el-option label="其他" :value="3" />
        </el-select>
        <el-select v-model="filters.status" placeholder="处理状态" clearable class="w-28">
          <el-option label="全部" value="" />
          <el-option label="已入库" :value="0" />
          <el-option label="解析中" :value="1" />
          <el-option label="已完成" :value="2" />
          <el-option label="失败" :value="3" />
        </el-select>
        <el-input v-model="filters.keyword" placeholder="搜索文件名" clearable class="w-56" @clear="handleSearch" @keyup.enter="handleSearch">
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
      <el-button type="primary" @click="uploadDialogVisible = true">
        <el-icon><Upload /></el-icon>
        上传文档
      </el-button>
    </section>

    <!-- 文档列表 -->
    <section class="bg-white rounded-lg shadow-sm">
      <el-table
        v-loading="loading"
        :data="documentList"
        border
        stripe
        class="w-full"
        empty-text="知识库为空，请上传文档"
      >
        <el-table-column label="文档标题" min-width="150">
          <template #default="{ row }">
            <span class="text-blue-600 cursor-pointer hover:underline">{{ row.file_name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="文档类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getDocTypeTag(row.doc_type)" size="small">
              {{ getDocTypeLabel(row.doc_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="文件大小" width="100">
          <template #default="{ row }">
            {{ formatSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="切片数" width="80" />
        <el-table-column label="处理状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.status === 1" type="warning" size="small">解析中</el-tag>
            <el-tag v-else-if="row.status === 2" type="success" size="small">已完成</el-tag>
            <el-tag v-else-if="row.status === 3" type="danger" size="small">失败</el-tag>
            <el-tag v-else type="info" size="small">已入库</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="上传时间" width="170">
          <template #default="{ row }">
            {{ row.created_at || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" disabled>
              查看
            </el-button>
            <el-button text type="warning" size="small" disabled>
              重新处理
            </el-button>
            <el-button text type="danger" size="small" disabled>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-end p-4 border-t border-gray-200">
        <el-pagination
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @update:current-page="handlePageChange"
        />
      </div>
    </section>

    <!-- 上传文档对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传文档"
      width="650px"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="文档类型">
          <el-select v-model="uploadForm.docType" placeholder="请选择文档类型" class="w-full">
            <el-option label="标准规范" :value="0" />
            <el-option label="历史案例" :value="1" />
            <el-option label="处置预案" :value="2" />
            <el-option label="其他" :value="3" />
          </el-select>
        </el-form-item>

        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            drag
            multiple
            :auto-upload="false"
            accept=".pdf"
            :limit="10"
            :on-exceed="handleExceed"
            @change="handleFileChange"
          >
            <el-icon class="el-icon--upload" :size="40"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处，或 <em>点击选择</em>
            </div>
            <template #tip>
              <div class="el-upload__tip text-gray-400">
                支持 .pdf 格式，单文件不超过 50MB，单次最多 10 个文件
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="uploading"
          :disabled="uploadForm.docType === null"
          @click="handleUpload"
        >
          上传并处理
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 知识库管理页面
 * 功能描述：知识库文档的列表展示、筛选、上传
 * 依赖接口：GET /api/v1/documents, POST /api/v1/documents/upload
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Upload, UploadFilled } from '@element-plus/icons-vue'
import { uploadDocuments, getDocumentList } from '@/api/knowledge'

const uploadDialogVisible = ref(false)
const uploading = ref(false)
const uploadRef = ref(null)

const uploadForm = reactive({
  docType: null
})

const selectedFiles = ref([])

const loading = ref(false)
const documentList = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 15,
  total: 0,
  totalPages: 0
})
const filters = reactive({
  keyword: '',
  docType: null,
  status: null
})

const DOC_TYPE_MAP = {
  0: { label: '标准规范', tag: 'primary' },
  1: { label: '历史案例', tag: 'warning' },
  2: { label: '处置预案', tag: 'success' },
  3: { label: '其他', tag: 'info' }
}

function getDocTypeLabel(type) {
  return DOC_TYPE_MAP[type]?.label || '未知'
}

function getDocTypeTag(type) {
  return DOC_TYPE_MAP[type]?.tag || 'info'
}

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function handleExceed() {
  ElMessage.warning('单次最多上传 10 个文件')
}

function handleFileChange(uploadFile, uploadFiles) {
  selectedFiles.value = uploadFiles
}

function handleDialogClosed() {
  uploadForm.docType = null
  selectedFiles.value = []
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

function handleSearch() {
  pagination.page = 1
  fetchDocumentList()
}

function handlePageChange(page) {
  pagination.page = page
  fetchDocumentList()
}

async function fetchDocumentList() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.docType !== '') params.doc_type = filters.docType
    if (filters.status !== '') params.status = filters.status

    const res = await getDocumentList(params)
    documentList.value = res.data.lists
    pagination.total = res.data.pagination.total
    pagination.totalPages = res.data.pagination.total_pages
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleUpload() {
  if (uploadForm.docType === null) {
    ElMessage.warning('请选择文档类型')
    return
  }

  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    selectedFiles.value.forEach((file) => {
      formData.append('files', file.raw)
    })
    formData.append('category', uploadForm.docType)

    const res = await uploadDocuments(formData)
    const uploadData = res.data

    uploadDialogVisible.value = false
    ElMessage.success(`上传完成：成功 ${uploadData.success_count} 个` + (uploadData.failed_count > 0 ? `，失败 ${uploadData.failed_count} 个` : ''))
    fetchDocumentList()
  } catch (e) {
    ElMessage.error(e.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  fetchDocumentList()
})
</script>
