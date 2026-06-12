<template>
  <div class="join-page">
    <div class="join-card">
      <svg class="join-logo" viewBox="0 0 80 80" fill="none">
        <rect width="80" height="80" rx="20" fill="url(#joinGrad)"/>
        <path d="M52 28c-2-4-7-6-12-6-7 0-13 4-14 10-5 0-9 4-9 9s4 9 9 9h25c5 0 9-4 9-9s-4-9-8-9c0-2 0-4 0-4z" fill="#fff" opacity=".95"/>
        <defs><linearGradient id="joinGrad" x1="0" y1="0" x2="80" y2="80"><stop stop-color="#6366f1"/><stop offset="1" stop-color="#3b82f6"/></linearGradient></defs>
      </svg>

      <template v-if="loading">
        <ProgressSpinner strokeWidth="4" />
        <p class="join-status">加载中...</p>
      </template>

      <template v-else-if="error">
        <h2>链接已失效</h2>
        <p class="join-desc">{{ error }}</p>
        <Button label="返回首页" icon="pi pi-home" @click="goHome" />
      </template>

      <template v-else>
        <h2>{{ noteTitle }}</h2>
        <p class="join-desc">
          来自 <strong>{{ ownerName }}</strong> 的分享邀请
        </p>
        <div class="perm-badge">
          <i :class="permission === 'write' ? 'pi pi-pencil' : 'pi pi-eye'"></i>
          {{ permission === 'write' ? '可编辑' : '只读' }}
        </div>
        <Button
          label="加入协作"
          icon="pi pi-sign-in"
          :loading="joining"
          @click="joinNote"
          size="large"
          class="join-btn"
        />
        <p class="join-hint">以 <strong>{{ authStore.user?.username }}</strong> 的身份加入</p>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const token = route.params.token as string
const noteTitle = ref('')
const ownerName = ref('')
const permission = ref('read')
const loading = ref(true)
const joining = ref(false)
const error = ref('')

onMounted(async () => {
  if (!authStore.token) { router.push(`/login?redirect=/join/${token}`); return }
  loading.value = true
  try {
    const r = await api.get(`/share/${token}`)
    noteTitle.value = r.data.note_title
    ownerName.value = r.data.owner?.username || '未知'
    permission.value = r.data.permission
  } catch (e: any) {
    error.value = e.response?.data?.detail || '分享链接无效或已过期'
  } finally {
    loading.value = false
  }
})

async function joinNote() {
  joining.value = true
  try {
    // 通过分享链接获取 note_id
    const r = await api.get(`/share/${token}`)
    router.push(`/note/${r.data.note_id}`)
  } catch (e: any) {
    error.value = '加入失败'
  } finally {
    joining.value = false
  }
}

function goHome() { router.push('/') }
</script>

<style scoped>
.join-page {
  min-height:100vh; display:flex; align-items:center; justify-content:center;
  background:#f8fafc; padding:20px;
}
.join-card {
  background:#fff; border-radius:16px; padding:48px 40px;
  width:100%; max-width:440px; text-align:center;
  box-shadow:0 4px 40px rgba(0,0,0,.06);
  display:flex; flex-direction:column; align-items:center; gap:16px;
}
.join-logo { width:64px; height:64px; margin-bottom:8px; }
.join-card h2 { font-size:22px; font-weight:700; color:#0f172a; margin:0; }
.join-desc { font-size:14px; color:#64748b; margin:0; }
.join-status { color:#94a3b8; font-size:14px; }
.perm-badge {
  display:inline-flex; align-items:center; gap:6px;
  background:#eef2ff; color:#6366f1; font-size:13px; font-weight:600;
  padding:6px 14px; border-radius:20px;
}
.join-btn { width:100%; padding:14px; font-size:15px; font-weight:600; border-radius:10px; }
.join-hint { font-size:12px; color:#94a3b8; margin:0; }
</style>
