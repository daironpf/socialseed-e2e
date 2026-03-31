import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import TestExplorer from '../views/TestExplorer.vue'
import RunTests from '../views/RunTests.vue'
import History from '../views/History.vue'
import Settings from '../views/Settings.vue'
import LiveTraffic from '../views/LiveTraffic.vue'
import ManualTester from '../views/ManualTester.vue'
import AICommandCenter from '../views/AICommandCenter.vue'
import FlakinessDashboard from '../views/FlakinessDashboard.vue'
import TopologyGraph from '../views/TopologyGraph.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/tests', name: 'Tests', component: TestExplorer },
  { path: '/run', name: 'Run', component: RunTests },
  { path: '/history', name: 'History', component: History },
  { path: '/settings', name: 'Settings', component: Settings },
  { path: '/live-traffic', name: 'LiveTraffic', component: LiveTraffic },
  { path: '/manual-tester', name: 'ManualTester', component: ManualTester },
  { path: '/ai-command', name: 'AICommandCenter', component: AICommandCenter },
  { path: '/flakiness', name: 'FlakinessDashboard', component: FlakinessDashboard },
  { path: '/topology', name: 'TopologyGraph', component: TopologyGraph },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
