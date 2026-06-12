<template>
  <div class="auth-page">
    <!-- 左侧品牌区 -->
    <div class="auth-brand">
      <div class="brand-inner">
        <svg class="brand-logo" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="80" height="80" rx="20" fill="url(#logoGrad2)"/>
          <path d="M52 28c-2-4-7-6-12-6-7 0-13 4-14 10-5 0-9 4-9 9s4 9 9 9h25c5 0 9-4 9-9s-4-9-8-9c0-2 0-4 0-4z" fill="#fff" opacity=".95"/>
          <defs><linearGradient id="logoGrad2" x1="0" y1="0" x2="80" y2="80"><stop stop-color="#6366f1"/><stop offset="1" stop-color="#3b82f6"/></linearGradient></defs>
        </svg>
        <h1 class="brand-title">加入云笔记</h1>
        <p class="brand-desc">免费注册，开启实时协作之旅</p>
      </div>
    </div>

    <!-- 右侧注册区 -->
    <div class="auth-form-wrap">
      <div class="auth-card">
        <h2 class="form-title">创建账号</h2>
        <p class="form-sub">填写信息注册新账号</p>

        <div class="form-fields">
          <div class="field">
            <label>用户名</label>
            <InputText v-model="username" placeholder="2-50个字符" class="w-full" size="large" @keyup.enter="handleRegister" />
          </div>
          <div class="field">
            <label>密码</label>
            <Password v-model="password" placeholder="至少4位" :feedback="false" toggleMask class="w-full" size="large" @keyup.enter="handleRegister" />
          </div>
          <div class="field">
            <label>确认密码</label>
            <Password v-model="confirmPassword" placeholder="再次输入密码" :feedback="false" toggleMask class="w-full" size="large" @keyup.enter="handleRegister" />
          </div>

          <Message v-if="error" severity="error" :closable="true" @close="error=''">{{ error }}</Message>

          <Button
            label="注 册"
            icon="pi pi-user-plus"
            :loading="loading"
            class="w-full submit-btn"
            size="large"
            @click="handleRegister"
          />
        </div>

        <div class="form-footer">
          已有账号？<router-link to="/login" class="link">返回登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  if (!username.value || !password.value) { error.value = '请填写用户名和密码'; return }
  if (password.value !== confirmPassword.value) { error.value = '两次密码不一致'; return }
  if (password.value.length < 4) { error.value = '密码至少4位'; return }

  loading.value = true; error.value = ''
  try {
    const res = await api.post('/auth/register', { username: username.value, password: password.value })
    authStore.setAuth(res.data.access_token, res.data.user)
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '注册失败'
  } finally { loading.value = false }
}
</script>

<style scoped>
.auth-page { min-height:100vh; display:flex; background:#fff; }
.auth-brand {
  flex:1; background:linear-gradient(135deg,#6366f1 0%,#3b82f6 50%,#06b6d4 100%);
  display:flex; align-items:center; justify-content:center;
  position:relative; overflow:hidden;
}
.auth-brand::before {
  content:''; position:absolute; top:-50%; right:-30%;
  width:600px; height:600px; border-radius:50%;
  background:rgba(255,255,255,.06);
}
.auth-brand::after {
  content:''; position:absolute; bottom:-20%; left:-10%;
  width:400px; height:400px; border-radius:50%;
  background:rgba(255,255,255,.04);
}
.brand-inner { text-align:center; position:relative; z-index:1; }
.brand-logo { width:80px; height:80px; margin-bottom:24px; filter:drop-shadow(0 8px 24px rgba(0,0,0,.15)); }
.brand-title { font-size:36px; font-weight:800; color:#fff; margin:0 0 8px; letter-spacing:-1px; }
.brand-desc { font-size:15px; color:rgba(255,255,255,.75); margin:0; }

.auth-form-wrap {
  width:480px; display:flex; align-items:center; justify-content:center;
  padding:40px;
}
.auth-card { width:100%; max-width:380px; }
.form-title { font-size:26px; font-weight:700; color:#0f172a; margin:0 0 4px; }
.form-sub { font-size:14px; color:#64748b; margin:0 0 32px; }

.form-fields .field { margin-bottom:20px; }
.form-fields label { display:block; font-size:13px; font-weight:600; color:#334155; margin-bottom:6px; text-transform:uppercase; letter-spacing:.5px; }

.submit-btn {
  margin-top:12px; padding:14px;
  font-size:15px; font-weight:600; border-radius:10px;
  background:linear-gradient(135deg,#6366f1,#3b82f6)!important;
  border:none!important; transition:all .2s;
}
.submit-btn:hover { transform:translateY(-1px); box-shadow:0 8px 24px rgba(99,102,241,.3)!important; }

.form-footer { text-align:center; margin-top:28px; font-size:14px; color:#64748b; }
.link { color:#6366f1; font-weight:600; text-decoration:none; }
.link:hover { text-decoration:underline; }
.w-full { width:100%; }

@media(max-width:768px) {
  .auth-brand { display:none; }
  .auth-form-wrap { width:100%; padding:24px; }
}
</style>
