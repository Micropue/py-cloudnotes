import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('../views/RegisterView.vue'),
      meta: { guest: true },
    },
    {
      path: '/join/:token',
      name: 'Join',
      component: () => import('../views/JoinView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/',
      name: 'NotesList',
      component: () => import('../views/NotesListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/note/:id',
      name: 'NoteEditor',
      component: () => import('../views/NoteEditorView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.token) {
    // 保存重定向路径
    const redirect = to.fullPath
    next(`/login?redirect=${encodeURIComponent(redirect)}`)
  } else if (to.meta.guest && authStore.token) {
    next('/')
  } else {
    next()
  }
})

export default router
