<template>
  <div class="editor-page">
    <header class="editor-topbar">
      <div class="top-left">
        <Button icon="pi pi-arrow-left" severity="secondary" text rounded @click="goBack" v-tooltip.bottom="'返回列表'" />
        <InputText
          v-model="noteTitle"
          class="title-input"
          placeholder="未命名笔记"
          @blur="saveTitle"
          @keyup.enter="($event.target as HTMLInputElement).blur()"
        />
        <span class="save-status" :class="{ saved: isSaved }">
          <i :class="isSaved ? 'pi pi-check-circle' : 'pi pi-circle-fill'" :style="{ color: isSaved ? '#10b981' : '#f59e0b', fontSize: '10px' }"></i>
          {{ isSaved ? '已保存' : '编辑中' }}
        </span>
      </div>
      <div class="top-right">
        <!-- 协作者头像列表 -->
        <div class="collab-avatars" v-if="collaborators.length > 1">
          <div v-for="c in collaborators" :key="c.user_id" class="collab-avatar-item" v-tooltip.top="c.username + (c.is_online ? ' · 在线' : '')">
            <Avatar :image="c.avatar_url" :label="c.username?.charAt(0).toUpperCase()" shape="circle" size="normal" />
            <span class="collab-dot" :class="{ online: c.is_online }"></span>
          </div>
        </div>
        <div class="user-badge">
          <Avatar :image="authStore.user?.avatar_url" :label="authStore.user?.username?.charAt(0).toUpperCase()" shape="circle" size="normal" />
          <span class="uname">{{ authStore.user?.username }}</span>
        </div>
        <Button icon="pi pi-share-alt" severity="secondary" text rounded size="small" v-tooltip.top="'分享'" @click="showShareDialog = true" />
        <Button icon="pi pi-sign-out" severity="secondary" text rounded size="small" v-tooltip.top="'退出'" @click="handleLogout" />
      </div>
    </header>

    <div class="editor-main">
      <div class="editor-panel">
        <div class="panel-toolbar">
          <span class="panel-label"><i class="pi pi-pencil" style="margin-right:6px"></i>Markdown 编辑</span>
          <div class="toolbar-buttons">
            <Button icon="pi pi-bold" severity="secondary" text rounded size="small" @click="insertMD('**','**')" v-tooltip.top="'加粗'" />
            <Button icon="pi pi-italic" severity="secondary" text rounded size="small" @click="insertMD('*','*')" v-tooltip.top="'斜体'" />
            <Button icon="pi pi-minus" severity="secondary" text rounded size="small" @click="insertMD('\n## ','')" v-tooltip.top="'标题'" />
            <Button icon="pi pi-list" severity="secondary" text rounded size="small" @click="insertMD('\n- ','')" v-tooltip.top="'列表'" />
            <Button icon="pi pi-code" severity="secondary" text rounded size="small" @click="insertMD('`','`')" v-tooltip.top="'代码'" />
            <Button icon="pi pi-link" severity="secondary" text rounded size="small" @click="insertMD('[','](url)')" v-tooltip.top="'链接'" />
            <Button icon="pi pi-image" severity="secondary" text rounded size="small" @click="insertMD('![alt](','url)')" v-tooltip.top="'图片'" />
          </div>
        </div>
        <div class="editor-wrapper" ref="editorWrapper">
          <textarea
            ref="editorRef"
            class="editor-textarea"
            :value="editorContent"
            placeholder="开始写 Markdown..."
            @input="onEditorInput"
            @keydown="scheduleCursor"
            @click="updateCursor"
            @mouseup="updateCursor"
            @scroll="syncScroll"
          ></textarea>
          <div v-for="c in remoteCursors" :key="c.userId" class="remote-cursor" :style="cursorStyle(c)">
            <div class="cursor-label" :style="{ background: c.color }">{{ c.username }}</div>
            <div class="cursor-caret" :style="{ background: c.color }"></div>
          </div>
        </div>
      </div>
      <div class="preview-panel" ref="previewRef" @scroll="syncPreviewScroll">
        <div class="panel-toolbar">
          <span class="panel-label"><i class="pi pi-eye" style="margin-right:6px"></i>实时预览</span>
        </div>
        <div class="preview-content" v-html="renderedMD"></div>
      </div>
    </div>

    <div class="comment-fab" @click="showComments = !showComments">
      <Button :icon="showComments ? 'pi pi-times' : 'pi pi-comments'" :severity="showComments ? 'danger' : 'secondary'" rounded raised v-tooltip.left="showComments ? '关闭' : '评论'" />
      <span v-if="!showComments && commentCount > 0" class="comment-badge">{{ commentCount }}</span>
    </div>

    <transition name="slide">
      <div v-if="showComments" class="comment-sidebar">
        <CommentSection :note-id="noteId" @update="loadCommentCount" ref="commentRef" />
      </div>
    </transition>

    <ShareLinkDialog v-model:visible="showShareDialog" :note-id="noteId" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'
import Avatar from 'primevue/avatar'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useAuthStore } from '../stores/auth'
import { collabWS } from '../services/websocket'
import api from '../services/api'
import CommentSection from '../components/CommentSection.vue'
import ShareLinkDialog from '../components/ShareLinkDialog.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const noteId = Number(route.params.id)
const md = new MarkdownIt({ breaks: true, linkify: true })

const noteTitle = ref('…')
const editorContent = ref('')
const isSaved = ref(true)
const editorRef = ref<HTMLTextAreaElement | null>(null)
const editorWrapper = ref<HTMLDivElement | null>(null)
const previewRef = ref<HTMLDivElement | null>(null)
const showComments = ref(false)
const showShareDialog = ref(false)
const commentCount = ref(0)
const commentRef = ref<InstanceType<typeof CommentSection> | null>(null)

interface RCursor { userId: number; username: string; line: number; col: number; color: string; top?: number; left?: number }
const remoteCursors = ref<RCursor[]>([])
const onlineUsers = ref<any[]>([])
const collaborators = ref<any[]>([])
const cursorColors = ['#6366f1','#f59e0b','#10b981','#ef4444','#8b5cf6','#ec4899','#06b6d4','#f97316']

let scrollingEditor = false, scrollingPreview = false

function calcCursorPos(el: HTMLTextAreaElement, pos: number): { top: number; left: number } {
  const cs = getComputedStyle(el)
  const font = `${cs.fontSize} ${cs.fontFamily}`
  const lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.5
  const pl = parseFloat(cs.paddingLeft) || 20
  const pt = parseFloat(cs.paddingTop) || 20
  const text = el.value.substring(0, pos)
  const lines = text.split('\n')
  const lastLine = lines[lines.length - 1]
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')!
  ctx.font = font
  const lw = ctx.measureText(lastLine).width
  return { top: (lines.length - 1) * lh + pt - el.scrollTop, left: lw + pl }
}

function cursorStyle(c: RCursor) {
  const el = editorRef.value
  if (!el) return { display: 'none' }
  const lines = editorContent.value.split('\n')
  const li = Math.min(c.line - 1, lines.length - 1)
  const lt = lines[li] || ''
  const col = Math.min(c.col, lt.length)
  const fullText = lines.slice(0, li).join('\n') + (li > 0 ? '\n' : '') + lt.substring(0, col)
  const { top, left } = calcCursorPos(el, fullText.length)
  return { top: `${top}px`, left: `${left}px` }
}

onMounted(async () => {
  try {
    const res = await api.get(`/notes/${noteId}`)
    noteTitle.value = res.data.title
    editorContent.value = res.data.content || ''
  } catch { router.push('/'); return }

  const { ytext } = collabWS.connect(noteId)
  collabWS.onRemoteChange((content) => { editorContent.value = content })
  collabWS.onAwareness((users) => {
    onlineUsers.value = users
    const cursors: RCursor[] = []
    users.forEach((u, i) => {
      if (u.user_id !== authStore.user?.id && u.cursor) {
        cursors.push({ userId: u.user_id, username: u.username, line: u.cursor.line, col: u.cursor.col, color: cursorColors[i % cursorColors.length] })
      }
    })
    remoteCursors.value = cursors
  })

  await loadCommentCount()
  await loadCollaborators()
  nextTick(() => updateCursor())

  // 每10秒刷新协作者列表
  collabTimer = setInterval(loadCollaborators, 10000)
})

let collabTimer: any
onUnmounted(() => { collabWS.saveContent(); collabWS.disconnect(); clearInterval(autoSaveTimer); clearInterval(collabTimer) })

function onEditorInput(e: Event) {
  const target = e.target as HTMLTextAreaElement
  editorContent.value = target.value
  isSaved.value = false
  collabWS.syncLocalChange(target.value)
  scheduleCursor()
}

function scheduleCursor() { nextTick(() => updateCursor()) }
function updateCursor() {
  const el = editorRef.value; if (!el) return
  const p = el.selectionStart
  const before = editorContent.value.substring(0, p)
  const line = before.split('\n').length
  const lastNL = before.lastIndexOf('\n')
  collabWS.setCursor(line, p - lastNL)
}

function insertMD(before: string, after: string) {
  const el = editorRef.value; if (!el) return
  const s = el.selectionStart, e = el.selectionEnd
  const sel = editorContent.value.substring(s, e)
  const ins = before + sel + after
  editorContent.value = editorContent.value.substring(0, s) + ins + editorContent.value.substring(e)
  collabWS.syncLocalChange(editorContent.value)
  nextTick(() => { el.focus(); el.selectionStart = el.selectionEnd = s + before.length + sel.length; updateCursor() })
}

function syncScroll() {
  if (scrollingPreview) return; scrollingEditor = true
  const el = editorRef.value, pv = previewRef.value
  if (!el || !pv) { scrollingEditor = false; return }
  const ratio = el.scrollTop / (el.scrollHeight - el.clientHeight)
  pv.scrollTop = ratio * (pv.scrollHeight - pv.clientHeight)
  requestAnimationFrame(() => { scrollingEditor = false })
}
function syncPreviewScroll() {
  if (scrollingEditor) return; scrollingPreview = true
  const el = editorRef.value, pv = previewRef.value
  if (!el || !pv) { scrollingPreview = false; return }
  const ratio = pv.scrollTop / (pv.scrollHeight - pv.clientHeight)
  el.scrollTop = ratio * (el.scrollHeight - el.clientHeight)
  requestAnimationFrame(() => { scrollingPreview = false })
}

async function saveTitle() { try { await api.put(`/notes/${noteId}`, { title: noteTitle.value }) } catch {} }
const autoSaveTimer = setInterval(() => {
  if (!isSaved.value) {
    api.put(`/notes/${noteId}`, { content: editorContent.value }).then(() => { isSaved.value = true }).catch(() => {})
    collabWS.saveContent()
  }
}, 8000)

async function loadCommentCount() { try { const r = await api.get(`/notes/${noteId}/comments`); commentCount.value = r.data.length } catch {} }
async function loadCollaborators() { try { const r = await api.get(`/notes/${noteId}/collaborators`); collaborators.value = r.data } catch {} }

function goBack() { collabWS.saveContent(); router.push('/') }
function handleLogout() { collabWS.disconnect(); authStore.logout(); router.push('/login') }

const renderedMD = computed(() => {
  try { return md.render(editorContent.value || '') }
  catch { return '<p style="color:#ef4444">渲染错误</p>' }
})
</script>

<style scoped>
.editor-page { height:100vh; display:flex; flex-direction:column; background:#f8fafc; }
.editor-topbar {
  display:flex; align-items:center; justify-content:space-between;
  padding:8px 20px; background:#fff; border-bottom:1px solid #e2e8f0;
  flex-shrink:0; z-index:50;
}
.top-left,.top-right { display:flex; align-items:center; gap:8px; }
.title-input { border:none!important; box-shadow:none!important; font-size:17px; font-weight:700; padding:6px 10px; background:transparent; width:240px; }
.title-input:focus { background:#f1f5f9; border-radius:6px; }
.save-status { font-size:12px; color:#94a3b8; white-space:nowrap; display:flex; align-items:center; gap:4px; }
.save-status.saved { color:#10b981; }
.collab-avatars { display:flex; align-items:center; gap:2px; }
.collab-avatar-item { position:relative; }
.collab-avatar-item + .collab-avatar-item { margin-left:-6px; }
.collab-dot {
  position:absolute; bottom:-1px; right:-1px;
  width:9px; height:9px; border-radius:50%; background:#cbd5e1;
  border:2px solid #fff;
}
.collab-dot.online { background:#10b981; }
.user-badge { display:flex; align-items:center; gap:8px; }
.uname { font-size:13px; font-weight:600; color:#334155; }

.editor-main { flex:1; display:flex; overflow:hidden; }
.editor-panel,.preview-panel { flex:1; display:flex; flex-direction:column; }
.editor-panel { border-right:1px solid #e2e8f0; }
.panel-toolbar {
  display:flex; align-items:center; justify-content:space-between;
  padding:7px 16px; background:#f1f5f9; border-bottom:1px solid #e2e8f0;
  flex-shrink:0;
}
.panel-label { font-size:13px; font-weight:600; color:#475569; display:flex; align-items:center; }
.toolbar-buttons { display:flex; gap:2px; }

.editor-wrapper { flex:1; position:relative; overflow:hidden; }
.editor-textarea {
  width:100%; height:100%; border:none; outline:none; resize:none;
  padding:20px; font-family:'JetBrains Mono','Fira Code','Cascadia Code',monospace;
  font-size:14px; line-height:1.7; background:#fafbfc; color:#1e293b;
  tab-size:2;
}

.remote-cursor { position:absolute; pointer-events:none; z-index:10; }
.cursor-label { color:#fff; font-size:10px; padding:1px 6px; border-radius:4px 4px 4px 0; white-space:nowrap; position:absolute; top:-17px; left:0; }
.cursor-caret { width:2px; height:20px; }

.preview-content { flex:1; padding:20px 28px; overflow-y:auto; line-height:1.8; color:#334155; }
.preview-content :deep(h1){ font-size:2em; margin:.67em 0; font-weight:700; border-bottom:2px solid #e2e8f0; padding-bottom:8px; }
.preview-content :deep(h2){ font-size:1.5em; margin:.75em 0 .5em; font-weight:700; color:#1e293b; }
.preview-content :deep(h3){ font-size:1.17em; margin:.5em 0; font-weight:600; }
.preview-content :deep(p){ margin:.5em 0; }
.preview-content :deep(code){ background:#f1f5f9; padding:2px 6px; border-radius:4px; font-size:.9em; color:#6366f1; }
.preview-content :deep(pre){ background:#1e293b; color:#e2e8f0; padding:16px; border-radius:8px; overflow-x:auto; margin:12px 0; }
.preview-content :deep(pre code){ background:none; padding:0; color:inherit; }
.preview-content :deep(blockquote){ border-left:3px solid #6366f1; padding-left:16px; color:#64748b; margin:12px 0; background:#f8fafc; padding:8px 16px; border-radius:0 6px 6px 0; }
.preview-content :deep(ul),.preview-content :deep(ol){ padding-left:24px; margin:8px 0; }
.preview-content :deep(a){ color:#6366f1; text-decoration:underline; }
.preview-content :deep(img){ max-width:100%; border-radius:8px; }
.preview-content :deep(table){ border-collapse:collapse; width:100%; margin:12px 0; }
.preview-content :deep(th),.preview-content :deep(td){ border:1px solid #e2e8f0; padding:8px 12px; text-align:left; }
.preview-content :deep(th){ background:#f8fafc; font-weight:600; }

.comment-fab { position:fixed; bottom:28px; right:28px; z-index:200; }
.comment-badge {
  position:absolute; top:-6px; right:-6px;
  background:#ef4444; color:#fff; font-size:11px; font-weight:700;
  min-width:18px; height:18px; border-radius:9px;
  display:flex; align-items:center; justify-content:center;
}
.comment-sidebar {
  position:fixed; right:0; top:0; bottom:0; width:380px;
  background:#fff; border-left:1px solid #e2e8f0;
  box-shadow:-4px 0 20px rgba(0,0,0,.06); z-index:150; overflow-y:auto;
}
.slide-enter-active,.slide-leave-active { transition:transform .25s ease; }
.slide-enter-from,.slide-leave-to { transform:translateX(100%); }
</style>
