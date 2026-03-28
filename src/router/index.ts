import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { logger } from '@/utils/logger'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
  },
  {
    path: '/',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const accessToken = localStorage.getItem('yumi_access_token')
  const requiresAuth = to.meta.requiresAuth

  logger.info('Router', 'Navigation', {
    to: to.path,
    from: from.path,
    requiresAuth,
    hasToken: !!accessToken,
  })

  if (requiresAuth && !accessToken) {
    logger.info('Router', 'Redirecting to login')
    next('/login')
    return
  }

  if (to.path === '/login' && accessToken) {
    logger.info('Router', 'Already logged in, redirecting to chat')
    next('/')
    return
  }

  next()
})

export default router
