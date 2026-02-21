import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import TestExplorer from '../views/TestExplorer.vue'
import RunTests from '../views/RunTests.vue'
import History from '../views/History.vue'
import Settings from '../views/Settings.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/tests', name: 'Tests', component: TestExplorer },
  { path: '/run', name: 'Run', component: RunTests },
  { path: '/history', name: 'History', component: History },
  { path: '/settings', name: 'Settings', component: Settings }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
