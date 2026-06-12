<template>
  <Dialog
    :visible="visible"
    @update:visible="$emit('update:visible', $event)"
    header="分享笔记"
    :modal="true"
    :style="{ width: '460px' }"
    :draggable="false"
  >
    <div class="share-content">
      <!-- 权限配置 -->
      <div class="section">
        <label class="section-label"><i class="pi pi-lock" style="margin-right:6px"></i>权限设置</label>
        <SelectButton
          v-model="permission"
          :options="permOptions"
          optionLabel="label"
          optionValue="value"
          :disabled="!!shareUrl"
        />
      </div>

      <!-- 已生成链接 → 显示链接 + 复制 + 撤销 -->
      <div v-if="shareUrl" class="section">
        <label class="section-label"><i class="pi pi-link" style="margin-right:6px"></i>分享链接</label>
        <div class="link-row">
          <InputText :value="shareUrl" readonly class="link-input" />
          <Button icon="pi pi-copy" severity="info" @click="copyLink" v-tooltip.top="'复制链接'" />
        </div>
        <div class="link-actions">
          <Button
            label="停止分享"
            icon="pi pi-stop-circle"
            severity="danger"
            outlined
            size="small"
            @click="revokeLink"
            :loading="revoking"
          />
          <span class="link-status" v-if="shareActive">
            <i class="pi pi-check-circle" style="color:#10b981"></i> 分享中
          </span>
        </div>
      </div>

      <!-- 未生成 → 生成按钮 -->
      <div v-else class="section">
        <Button
          label="生成分享链接"
          icon="pi pi-link"
          @click="createLink"
          :loading="creating"
          class="w-full"
        />
      </div>

      <!-- 协作者列表 -->
      <div class="section">
        <label class="section-label">
          <i class="pi pi-users" style="margin-right:6px"></i>协作者
          <span class="collab-count">{{ collaborators.length }}</span>
        </label>
        <div class="collab-list" v-if="collaborators.length > 0">
          <div v-for="c in collaborators" :key="c.user_id" class="collab-item">
            <div class="collab-avatar-wrap">
              <Avatar :image="c.avatar_url" :label="c.username?.charAt(0).toUpperCase()" shape="circle" size="normal" />
              <span class="online-dot" :class="{ online: c.is_online }"></span>
            </div>
            <div class="collab-info">
              <span class="collab-name">{{ c.username }}</span>
              <span class="collab-role">{{ roleLabel(c.permission) }}</span>
            </div>
          </div>
        </div>
        <div v-else class="no-collab">
          <span>暂无其他协作者</span>
        </div>
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import Dialog from 'primevue/dialog'
import SelectButton from 'primevue/selectbutton'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Avatar from 'primevue/avatar'
import api from '../services/api'

const props = defineProps<{
  visible: boolean
  noteId: number
}>()

const emit = defineEmits(['update:visible'])

const permission = ref('read')
const shareUrl = ref('')
const shareToken = ref('')
const shareActive = ref(false)
const creating = ref(false)
const revoking = ref(false)
const collaborators = ref<any[]>([])

const permOptions = [
  { label: '可读', value: 'read' },
  { label: '可写', value: 'write' },
]

const roleLabel = (p: string) => {
  if (p === 'owner') return '所有者'
  if (p === 'write') return '可编辑'
  return '可读'
}

async function loadState() {
  // 加载协作者
  try {
    const r = await api.get(`/notes/${props.noteId}/collaborators`)
    collaborators.value = r.data
  } catch {}

  // 加载已有的分享链接
  try {
    const r = await api.get(`/notes/${props.noteId}/share-link`)
    shareToken.value = r.data.token
    permission.value = r.data.permission
    shareActive.value = r.data.is_active
    shareUrl.value = `${window.location.origin}/join/${r.data.token}`
  } catch {
    shareUrl.value = ''
    shareToken.value = ''
    shareActive.value = false
  }
}

async function createLink() {
  creating.value = true
  try {
    const r = await api.post(`/notes/${props.noteId}/share-link`, {
      permission: permission.value,
    })
    shareToken.value = r.data.token
    shareActive.value = true
    shareUrl.value = `${window.location.origin}/join/${r.data.token}`
  } catch (e: any) {
    alert(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function revokeLink() {
  revoking.value = true
  try {
    await api.delete(`/notes/${props.noteId}/share-link`)
    shareUrl.value = ''
    shareToken.value = ''
    shareActive.value = false
  } catch (e: any) {
    alert(e.response?.data?.detail || '撤销失败')
  } finally {
    revoking.value = false
  }
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    alert('链接已复制到剪贴板！')
  } catch {
    // fallback
    const el = document.createElement('textarea')
    el.value = shareUrl.value
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
    alert('链接已复制！')
  }
}

watch(() => props.visible, (v) => { if (v) loadState() })
onMounted(() => { if (props.visible) loadState() })
</script>

<style scoped>
.share-content { display:flex; flex-direction:column; gap:20px; }
.section { }
.section-label { font-size:13px; font-weight:600; color:#334155; display:flex; align-items:center; margin-bottom:10px; }

.link-row { display:flex; gap:8px; }
.link-input { flex:1; font-size:13px; font-family:monospace; }
.link-actions { display:flex; align-items:center; gap:12px; margin-top:10px; }
.link-status { font-size:12px; color:#64748b; display:flex; align-items:center; gap:4px; }

.collab-count {
  display:inline-flex; align-items:center; justify-content:center;
  background:#e2e8f0; color:#475569; font-size:11px; font-weight:700;
  min-width:20px; height:20px; border-radius:10px; margin-left:8px;
}
.collab-list { display:flex; flex-direction:column; gap:8px; }
.collab-item { display:flex; align-items:center; gap:10px; padding:8px; background:#f8fafc; border-radius:8px; }
.collab-avatar-wrap { position:relative; }
.online-dot {
  position:absolute; bottom:0; right:0;
  width:10px; height:10px; border-radius:50%; background:#cbd5e1;
  border:2px solid #fff;
}
.online-dot.online { background:#10b981; }
.collab-info { display:flex; flex-direction:column; }
.collab-name { font-size:14px; font-weight:600; color:#1e293b; }
.collab-role { font-size:11px; color:#94a3b8; }
.no-collab { font-size:13px; color:#94a3b8; padding:12px; text-align:center; }

.w-full { width:100%; }
</style>
