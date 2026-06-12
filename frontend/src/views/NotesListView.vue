<template>
  <div class="notes-page">
    <!-- 顶部导航 -->
    <header class="top-bar">
      <div class="top-left">
        <svg class="nav-logo" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="url(#navGrad)"/>
          <path d="M21 11c-1-2-3-3-5-3-3 0-5 2-6 4-2 0-4 1.5-4 3.5s1.5 3.5 3.5 3.5H20c2 0 3.5-1.5 3.5-3.5S22 12 20 12c0-1 0-1 0-1z" fill="#fff"/>
          <defs><linearGradient id="navGrad" x1="0" y1="0" x2="32" y2="32"><stop stop-color="#6366f1"/><stop offset="1" stop-color="#3b82f6"/></linearGradient></defs>
        </svg>
        <span class="brand">云笔记</span>
      </div>
      <div class="top-right">
        <div class="user-badge">
          <Avatar :image="authStore.user?.avatar_url" :label="authStore.user?.username?.charAt(0).toUpperCase()" shape="circle" size="normal" />
          <span class="username">{{ authStore.user?.username }}</span>
        </div>
        <Button icon="pi pi-sign-out" severity="secondary" text rounded size="small" v-tooltip.bottom="'退出登录'" @click="handleLogout" />
      </div>
    </header>

    <!-- 主内容 -->
    <main class="notes-main">
      <div class="notes-header">
        <h2><i class="pi pi-file-edit" style="margin-right:10px;color:#6366f1"></i>我的笔记</h2>
        <Button label="新建笔记" icon="pi pi-plus" @click="createNote" :loading="creating" />
      </div>

      <div v-if="notes.length === 0 && !loading" class="empty-state">
        <svg class="empty-icon" viewBox="0 0 80 80" fill="none">
          <rect x="20" y="8" width="40" height="56" rx="4" stroke="#cbd5e1" stroke-width="2" fill="none"/>
          <line x1="28" y1="22" x2="52" y2="22" stroke="#cbd5e1" stroke-width="2" stroke-linecap="round"/>
          <line x1="28" y1="30" x2="48" y2="30" stroke="#cbd5e1" stroke-width="2" stroke-linecap="round"/>
          <line x1="28" y1="38" x2="44" y2="38" stroke="#cbd5e1" stroke-width="2" stroke-linecap="round"/>
          <circle cx="55" cy="55" r="12" fill="#6366f1"/>
          <line x1="55" y1="49" x2="55" y2="61" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>
          <line x1="49" y1="55" x2="61" y2="55" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>
        </svg>
        <p>还没有笔记</p>
        <span>点击上方「新建笔记」按钮创建第一篇</span>
      </div>

      <div v-if="loading" class="loading-state">
        <ProgressSpinner strokeWidth="4" />
      </div>

      <div class="notes-grid">
        <div
          v-for="note in notes"
          :key="note.id"
          class="note-card"
          @click="openNote(note.id)"
        >
          <div class="note-card-header">
            <div class="note-title-row">
              <i class="pi pi-file" style="color:#6366f1;font-size:16px"></i>
              <h3>{{ note.title || '未命名笔记' }}</h3>
            </div>
            <Button
              icon="pi pi-trash"
              severity="danger"
              text
              rounded
              size="small"
              @click.stop="deleteNote(note.id)"
              v-tooltip.top="'删除'"
            />
          </div>
          <p class="note-card-preview">{{ getPreview(note) }}</p>
          <div class="note-card-meta">
            <Avatar :image="note.owner?.avatar_url" :label="note.owner?.username?.charAt(0).toUpperCase()" shape="circle" size="small" />
            <span>{{ note.owner?.username }}</span>
            <span class="dot">·</span>
            <i class="pi pi-clock" style="font-size:10px"></i>
            <span>{{ formatDate(note.updated_at) }}</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Avatar from 'primevue/avatar'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

interface NoteItem {
  id: number; title: string; owner_id: number; created_at: string; updated_at: string;
  owner?: { id: number; username: string; avatar_url: string }; content?: string
}

const notes = ref<NoteItem[]>([])
const loading = ref(true)
const creating = ref(false)

onMounted(() => loadNotes())

async function loadNotes() {
  loading.value = true
  try { const r = await api.get('/notes'); notes.value = r.data }
  catch {}
  finally { loading.value = false }
}

async function createNote() {
  creating.value = true
  try { const r = await api.post('/notes', { title:'未命名笔记',content:'' }); router.push(`/note/${r.data.id}`) }
  catch {}
  finally { creating.value = false }
}

async function deleteNote(id: number) {
  try { await api.delete(`/notes/${id}`); notes.value = notes.value.filter(n => n.id !== id) }
  catch {}
}

function openNote(id: number) { router.push(`/note/${id}`) }

function getPreview(n: NoteItem): string {
  return (n.content||'').replace(/[#*`>\-\[\]()!]/g,'').slice(0,100) || '空文档'
}

function formatDate(s: string): string {
  const d = new Date(s)
  return d.toLocaleDateString('zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})
}

function handleLogout() { authStore.logout(); router.push('/login') }
</script>

<style scoped>
.notes-page { min-height:100vh; display:flex; flex-direction:column; background:#f8fafc; }

.top-bar {
  display:flex; align-items:center; justify-content:space-between;
  padding:10px 24px; background:#fff; border-bottom:1px solid #e2e8f0;
  position:sticky; top:0; z-index:100;
}
.top-left { display:flex; align-items:center; gap:10px; }
.nav-logo { width:32px; height:32px; }
.brand { font-size:18px; font-weight:700; color:#1e293b; }
.top-right { display:flex; align-items:center; gap:10px; }
.user-badge { display:flex; align-items:center; gap:8px; }
.username { font-size:14px; font-weight:600; color:#334155; }

.notes-main { flex:1; max-width:800px; width:100%; margin:0 auto; padding:32px 24px; }
.notes-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:28px; }
.notes-header h2 { font-size:22px; font-weight:700; color:#0f172a; display:flex; align-items:center; }

.empty-state { text-align:center; padding:80px 20px; }
.empty-icon { width:80px; height:80px; margin-bottom:20px; }
.empty-state p { font-size:16px; font-weight:600; color:#64748b; margin:0 0 4px; }
.empty-state span { font-size:13px; color:#94a3b8; }

.loading-state { display:flex; justify-content:center; padding:60px; }

.notes-grid { display:flex; flex-direction:column; gap:10px; }

.note-card {
  background:#fff; border:1px solid #e2e8f0; border-radius:12px;
  padding:18px 22px; cursor:pointer; transition:all .15s;
}
.note-card:hover { border-color:#6366f1; box-shadow:0 4px 16px rgba(99,102,241,.1); transform:translateY(-1px); }

.note-card-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; }
.note-title-row { display:flex; align-items:center; gap:8px; }
.note-title-row h3 { font-size:15px; font-weight:600; color:#1e293b; margin:0; }

.note-card-preview { font-size:13px; color:#64748b; margin:0 0 10px; line-height:1.5; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

.note-card-meta { display:flex; align-items:center; gap:5px; font-size:12px; color:#94a3b8; }
.dot { color:#cbd5e1; }
</style>
