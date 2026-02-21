<template>
  <div class="app-container">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <h1 class="logo">
          <span class="logo-icon">🌱</span>
          <span class="logo-text" v-if="!sidebarCollapsed">SocialSeed</span>
        </h1>
        <button class="collapse-btn" @click="sidebarCollapsed = !sidebarCollapsed">
          {{ sidebarCollapsed ? '→' : '←' }}
        </button>
      </div>
      
      <nav class="nav-menu">
        <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
          <span class="nav-icon">📊</span>
          <span class="nav-text" v-if="!sidebarCollapsed">Dashboard</span>
        </router-link>
        <router-link to="/tests" class="nav-item" :class="{ active: $route.path === '/tests' }">
          <span class="nav-icon">🧪</span>
          <span class="nav-text" v-if="!sidebarCollapsed">Tests</span>
        </router-link>
        <router-link to="/run" class="nav-item" :class="{ active: $route.path === '/run' }">
          <span class="nav-icon">▶️</span>
          <span class="nav-text" v-if="!sidebarCollapsed">Run</span>
        </router-link>
        <router-link to="/history" class="nav-item" :class="{ active: $route.path === '/history' }">
          <span class="nav-icon">📜</span>
          <span class="nav-text" v-if="!sidebarCollapsed">History</span>
        </router-link>
        <router-link to="/settings" class="nav-item" :class="{ active: $route.path === '/settings' }">
          <span class="nav-icon">⚙️</span>
          <span class="nav-text" v-if="!sidebarCollapsed">Settings</span>
        </router-link>
      </nav>

      <div class="sidebar-footer" v-if="!sidebarCollapsed">
        <div class="connection-status" :class="{ connected: isConnected }">
          <span class="status-dot"></span>
          {{ isConnected ? 'Connected' : 'Disconnected' }}
        </div>
      </div>
    </aside>

    <main class="main-content">
      <header class="top-bar">
        <div class="breadcrumbs">
          <span class="breadcrumb-item">{{ currentRoute }}</span>
        </div>
        <div class="header-actions">
          <button class="btn btn-icon" @click="refreshData" :class="{ spinning: isRefreshing }">
            🔄
          </button>
          <div class="user-menu">
            <span class="user-avatar">👤</span>
          </div>
        </div>
      </header>

      <div class="content-area">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>

    <aside class="logs-panel" :class="{ expanded: logsExpanded }">
      <div class="logs-header" @click="logsExpanded = !logsExpanded">
        <span>📝 Live Logs</span>
        <span class="logs-count">{{ logCount }}</span>
      </div>
      <div class="logs-content" v-if="logsExpanded">
        <div class="log-filters">
          <button 
            v-for="level in ['all', 'info', 'success', 'error']" 
            :key="level"
            class="filter-btn"
            :class="{ active: logFilter === level }"
            @click="logFilter = level"
          >
            {{ level }}
          </button>
        </div>
        <div class="log-entries" ref="logContainer">
          <div 
            v-for="(log, index) in filteredLogs" 
            :key="index" 
            class="log-entry"
            :class="log.level"
          >
            <span class="log-time">{{ formatTime(log.timestamp) }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTestStore } from './stores/testStore'
import { useLogStore } from './stores/logStore'

const route = useRoute()
const testStore = useTestStore()
const logStore = useLogStore()

const sidebarCollapsed = ref(false)
const logsExpanded = ref(true)
const logFilter = ref('all')
const isRefreshing = ref(false)
const isConnected = ref(false)
const logContainer = ref(null)

const currentRoute = computed(() => {
  const routes = {
    '/': 'Dashboard',
    '/tests': 'Test Explorer',
    '/run': 'Run Tests',
    '/history': 'Run History',
    '/settings': 'Settings'
  }
  return routes[route.path] || 'Dashboard'
})

const logCount = computed(() => logStore.logs.length)

const filteredLogs = computed(() => {
  if (logFilter.value === 'all') return logStore.logs
  return logStore.logs.filter(l => l.level === logFilter.value)
})

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

const refreshData = async () => {
  isRefreshing.value = true
  await testStore.loadTests()
  isRefreshing.value = false
}

let ws = null

const connectWebSocket = () => {
  ws = new WebSocket(`ws://${window.location.host}/ws`)
  
  ws.onopen = () => {
    isConnected.value = true
    logStore.addLog('info', 'Connected to server')
  }
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'log') {
      logStore.addLog(data.level, data.message)
    } else if (data.type === 'test_result') {
      testStore.addResult(data.result)
    }
  }
  
  ws.onclose = () => {
    isConnected.value = false
    setTimeout(connectWebSocket, 3000)
  }
}

onMounted(() => {
  testStore.loadTests()
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) ws.close()
})
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
}

.sidebar {
  width: 260px;
  background: #1a1d23;
  color: white;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.25rem;
  margin: 0;
}

.logo-icon {
  font-size: 1.5rem;
}

.collapse-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 1rem;
}

.nav-menu {
  flex: 1;
  padding: 1rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  color: rgba(255,255,255,0.7);
  text-decoration: none;
  transition: all 0.2s;
}

.nav-item:hover, .nav-item.active {
  background: rgba(255,255,255,0.1);
  color: white;
}

.nav-icon {
  font-size: 1.25rem;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid rgba(255,255,255,0.1);
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: rgba(255,255,255,0.7);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
}

.connection-status.connected .status-dot {
  background: #22c55e;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.375rem;
}

.btn-icon:hover {
  background: #f3f4f6;
}

.btn-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.content-area {
  flex: 1;
  overflow: auto;
  padding: 1.5rem;
}

.logs-panel {
  width: 320px;
  background: #1a1d23;
  color: white;
  display: flex;
  flex-direction: column;
  border-left: 1px solid rgba(255,255,255,0.1);
}

.logs-panel.expanded {
  transform: translateX(0);
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.logs-count {
  background: rgba(255,255,255,0.2);
  padding: 0.125rem 0.5rem;
  border-radius: 1rem;
  font-size: 0.75rem;
}

.logs-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.log-filters {
  display: flex;
  gap: 0.25rem;
  padding: 0.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.filter-btn {
  background: none;
  border: none;
  color: rgba(255,255,255,0.7);
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.filter-btn.active {
  background: rgba(255,255,255,0.2);
  color: white;
}

.log-entries {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
}

.log-entry {
  padding: 0.25rem 0;
  display: flex;
  gap: 0.5rem;
}

.log-entry.info .log-message { color: #60a5fa; }
.log-entry.success .log-message { color: #4ade80; }
.log-entry.error .log-message { color: #f87171; }

.log-time {
  color: rgba(255,255,255,0.5);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
