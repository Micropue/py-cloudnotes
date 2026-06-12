<template>
  <div class="comment-section">
    <div class="comment-header">
      <h3><i class="pi pi-comments" style="margin-right:8px;color:#6366f1"></i>评论 ({{ comments.length }})</h3>
    </div>

    <div class="comment-list" ref="commentList">
      <div v-if="comments.length === 0" class="no-comments">
        <i class="pi pi-inbox" style="font-size:32px;color:#cbd5e1;display:block;margin-bottom:8px"></i>
        暂无评论
      </div>

      <div v-for="c in comments" :key="c.id" class="comment-item">
        <div class="comment-avatar">
          <Avatar :image="c.author?.avatar_url" :label="c.author?.username?.charAt(0).toUpperCase()" shape="circle" size="small" />
        </div>
        <div class="comment-body">
          <div class="comment-meta">
            <span class="comment-author">{{ c.author?.username }}</span>
            <span class="comment-time">{{ formatTime(c.created_at) }}</span>
          </div>
          <div class="comment-content">{{ c.content }}</div>
        </div>
      </div>
    </div>

    <div class="comment-input-area">
      <Textarea
        v-model="newComment"
        placeholder="输入评论... Enter 发送"
        rows="3"
        class="comment-textarea"
        @keydown="handleKeydown"
      />
      <Button
        label="发送"
        icon="pi pi-send"
        size="small"
        :loading="sending"
        :disabled="!newComment.trim()"
        @click="sendComment"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Avatar from 'primevue/avatar'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import api from '../services/api'

const props = defineProps<{ noteId: number }>()
const emit = defineEmits(['update'])

interface Comment {
  id: number; note_id: number; user_id: number; content: string; created_at: string;
  author?: { id: number; username: string; avatar_url: string }
}

const comments = ref<Comment[]>([])
const newComment = ref('')
const sending = ref(false)

async function loadComments() {
  try { const r = await api.get(`/notes/${props.noteId}/comments`); comments.value = r.data }
  catch {}
}

async function sendComment() {
  if (!newComment.value.trim()) return
  sending.value = true
  try {
    await api.post(`/notes/${props.noteId}/comments`, { content:newComment.value.trim() })
    newComment.value = ''
    await loadComments()
    emit('update')
  } catch {}
  finally { sending.value = false }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key==='Enter' && !e.shiftKey) { e.preventDefault(); sendComment() }
}

function formatTime(s: string): string {
  const diff = Date.now() - new Date(s).getTime()
  const m = Math.floor(diff/60000)
  if (m<1) return '刚刚'
  if (m<60) return `${m}分钟前`
  const h = Math.floor(m/60)
  if (h<24) return `${h}小时前`
  return new Date(s).toLocaleDateString('zh-CN',{month:'short',day:'numeric'})
}

defineExpose({ loadComments })

onMounted(() => { loadComments() })
</script>

<style scoped>
.comment-section { display:flex; flex-direction:column; height:100%; }
.comment-header { padding:16px 20px; border-bottom:1px solid #e2e8f0; }
.comment-header h3 { font-size:16px; font-weight:700; color:#1e293b; display:flex; align-items:center; }

.comment-list { flex:1; overflow-y:auto; padding:16px 20px; }
.no-comments { text-align:center; color:#94a3b8; padding:40px 0; font-size:14px; }

.comment-item { display:flex; gap:10px; margin-bottom:14px; padding-bottom:14px; border-bottom:1px solid #f1f5f9; }
.comment-item:last-child { border-bottom:none; }
.comment-avatar { flex-shrink:0; }
.comment-body { flex:1; }
.comment-meta { display:flex; align-items:center; gap:8px; margin-bottom:3px; }
.comment-author { font-weight:600; font-size:13px; color:#1e293b; }
.comment-time { font-size:11px; color:#94a3b8; }
.comment-content { font-size:14px; color:#334155; line-height:1.6; white-space:pre-wrap; }

.comment-input-area { padding:16px 20px; border-top:1px solid #e2e8f0; display:flex; flex-direction:column; gap:8px; }
.comment-textarea { width:100%; resize:none; }
</style>
