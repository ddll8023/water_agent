<template>
  <div class="login-bg min-h-screen flex items-center justify-center relative overflow-hidden">
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="caustic caustic-1"></div>
      <div class="caustic caustic-2"></div>
      <div class="caustic caustic-3"></div>
      <div class="particle particle-1"></div>
      <div class="particle particle-2"></div>
      <div class="particle particle-3"></div>
      <div class="particle particle-4"></div>
      <div class="particle particle-5"></div>
      <div class="particle particle-6"></div>
    </div>

    <div class="relative z-10 w-full max-w-md px-4">
      <div class="glass-card p-8 rounded-2xl">
        <div class="text-center mb-8">
          <div class="icon-ring mx-auto mb-5 flex h-16 w-16 items-center justify-center">
            <el-icon class="text-slate-600 text-3xl"><Monitor /></el-icon>
          </div>
          <h1 class="text-2xl font-bold text-slate-800 tracking-wide">水库水质智慧监测平台</h1>
          <p class="mt-2 text-sm text-slate-500">Reservoir Water Quality Monitoring</p>
        </div>

        <el-alert
          v-if="errorMessage"
          :title="errorMessage"
          type="error"
          :closable="true"
          show-icon
          class="mb-5 !rounded-lg !border !border-red-200 !bg-red-50 !text-red-700"
          @close="errorMessage = ''"
        />

        <el-form
          ref="formRef"
          :model="loginForm"
          :rules="formRules"
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username" class="dark-form-item">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
              size="large"
              class="glass-input"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item prop="password" class="dark-form-item">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
              size="large"
              class="glass-input"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item class="!mb-4">
            <el-button
              type="primary"
              size="large"
              class="login-btn w-full !h-12 !rounded-xl !text-base !font-semibold !tracking-wider"
              :loading="loading"
              :disabled="loading"
              @click="handleLogin"
            >
              {{ loading ? '正在登录...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="text-center">
          <router-link
            to="/register"
            class="text-sm text-slate-500 hover:text-slate-700 transition-colors duration-300 underline-offset-4 hover:underline"
          >
            还没有账号？立即注册
          </router-link>
        </div>
      </div>

      <p class="text-center text-xs text-slate-400 mt-6">v1.0.0</p>
    </div>
  </div>
</template>

<script setup>
/**
 * 登录页
 * 功能描述：水库水质监测系统统一登录入口，支持用户名+密码登录
 * 依赖组件：无
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, Lock, Monitor } from '@element-plus/icons-vue'
import { login } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)
const errorMessage = ref('')

const loginForm = reactive({
  username: '',
  password: ''
})

const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码不少于6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    const res = await login({
      username: loginForm.username,
      password: loginForm.password
    })
    authStore.setToken(res.data.access_token)
    authStore.setUserInfo({
      username: res.data.username
    })
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
  } catch (e) {
    const msg = e.message || '登录失败'
    if (msg.includes('用户名或密码') || msg.includes('密码错误') || msg.includes('不存在')) {
      errorMessage.value = '用户名或密码错误，请重试'
    } else if (msg.includes('禁用') || msg.includes('403')) {
      errorMessage.value = '账号已被禁用，请联系管理员'
    } else if (msg.includes('超时')) {
      errorMessage.value = '网络连接超时，请检查网络'
    } else if (msg.includes('网络')) {
      errorMessage.value = '网络连接失败，请检查网络设置'
    } else {
      errorMessage.value = '服务异常，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (authStore.isLoggedIn) {
    router.push('/dashboard')
  }
})
</script>

<style scoped>
.caustic {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.18;
  animation: causticFloat 12s ease-in-out infinite;
}

.caustic-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(148,163,184,0.5) 0%, transparent 70%);
  top: -10%;
  left: -15%;
  animation-delay: 0s;
}

.caustic-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(148,163,184,0.4) 0%, transparent 70%);
  bottom: -10%;
  right: -10%;
  animation-delay: -4s;
  animation-duration: 14s;
}

.caustic-3 {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(148,163,184,0.35) 0%, transparent 70%);
  top: 50%;
  left: 40%;
  animation-delay: -8s;
  animation-duration: 16s;
}

@keyframes causticFloat {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(30px, -20px) scale(1.15);
  }
  50% {
    transform: translate(-15px, 25px) scale(0.9);
  }
  75% {
    transform: translate(-25px, -10px) scale(1.1);
  }
}

.particle {
  position: absolute;
  border-radius: 50%;
  background: rgba(148, 163, 184, 0.2);
  animation: particleRise linear infinite;
}

.particle-1 {
  width: 4px;
  height: 4px;
  left: 10%;
  animation-duration: 8s;
  animation-delay: 0s;
}

.particle-2 {
  width: 3px;
  height: 3px;
  left: 25%;
  animation-duration: 10s;
  animation-delay: -2s;
}

.particle-3 {
  width: 5px;
  height: 5px;
  left: 45%;
  animation-duration: 7s;
  animation-delay: -4s;
}

.particle-4 {
  width: 3px;
  height: 3px;
  left: 65%;
  animation-duration: 11s;
  animation-delay: -6s;
}

.particle-5 {
  width: 4px;
  height: 4px;
  left: 80%;
  animation-duration: 9s;
  animation-delay: -3s;
}

.particle-6 {
  width: 2px;
  height: 2px;
  left: 90%;
  animation-duration: 12s;
  animation-delay: -7s;
}

@keyframes particleRise {
  0% {
    bottom: -10%;
    opacity: 0;
    transform: translateX(0);
  }
  20% {
    opacity: 0.5;
  }
  80% {
    opacity: 0.15;
  }
  100% {
    bottom: 110%;
    opacity: 0;
    transform: translateX(40px);
  }
}

.glass-card {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.06),
    0 1px 3px rgba(0, 0, 0, 0.04);
}

.icon-ring {
  border-radius: 50%;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border: 1px solid #cbd5e1;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  animation: iconGlow 4s ease-in-out infinite;
}

@keyframes iconGlow {
  0%, 100% {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  }
  50% {
    box-shadow: 0 2px 16px rgba(0, 0, 0, 0.1);
  }
}

.dark-form-item :deep(.el-form-item__label) {
  color: #475569;
}

.glass-input :deep(.el-input__wrapper) {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: none;
  transition: all 0.3s ease;
}

.glass-input :deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1;
  background: #fff;
}

.glass-input :deep(.el-input__wrapper.is-focus) {
  border-color: #0d9488;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.1);
}

.glass-input :deep(.el-input__inner) {
  color: #1e293b;
}

.glass-input :deep(.el-input__inner::placeholder) {
  color: #94a3b8;
}

.glass-input :deep(.el-input__prefix-inner .el-icon) {
  color: #94a3b8;
}

.glass-input :deep(.el-input__suffix .el-icon) {
  color: #94a3b8;
}

.login-btn {
  background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%) !important;
  border: none !important;
  color: #fff !important;
  letter-spacing: 0.15em;
  font-weight: 600 !important;
  transition: all 0.3s ease !important;
}

.login-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%) !important;
  box-shadow: 0 4px 20px rgba(13, 148, 136, 0.3);
  transform: translateY(-1px);
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
}

.login-btn.is-loading {
  background: linear-gradient(135deg, #0f766e 0%, #115e59 100%) !important;
}
</style>