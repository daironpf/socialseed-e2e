<template>
  <div class="flakiness-dashboard">
    <!-- EPIC-009: Real-Time Flakiness Detection & Self-Healing Dashboard -->
    
    <div class="dashboard-header">
      <h2>Flakiness Detection & Self-Healing</h2>
      <div class="header-actions">
        <button @click="refreshStats" class="btn-refresh">🔄 Refresh</button>
        <button @click="toggleAutoRefresh" :class="['btn-auto', { active: autoRefresh }]">
          {{ autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF' }}
        </button>
      </div>
    </div>
    
    <!-- Summary Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.totalTests }}</div>
        <div class="stat-label">Total Tests</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-value">{{ stats.flakyTests }}</div>
        <div class="stat-label">Flaky Tests</div>
      </div>
      <div class="stat-card success">
        <div class="stat-value">{{ stats.healedTests }}</div>
        <div class="stat-label">Healed</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.healingRate }}%</div>
        <div class="stat-label">Healing Rate</div>
      </div>
    </div>
    
    <!-- Flakiness Matrix -->
    <div class="section">
      <h3>Flakiness Matrix</h3>
      <table class="matrix-table">
        <thead>
          <tr>
            <th>Test Name</th>
            <th>Pass Rate</th>
            <th>Executions</th>
            <th>Avg Duration</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="test in flakyTests" :key="test.id" :class="getRowClass(test)">
            <td class="test-name">{{ test.name }}</td>
            <td>
              <div class="pass-rate-bar">
                <div class="fill" :style="{ width: test.passRate + '%' }"></div>
                <span>{{ test.passRate }}%</span>
              </div>
            </td>
            <td>{{ test.executions }}</td>
            <td>{{ test.avgDuration }}ms</td>
            <td>
              <span :class="['status-badge', test.status]">
                {{ getStatusLabel(test.status) }}
              </span>
            </td>
            <td>
              <button @click="healTest(test)" :disabled="test.status === 'healed'" class="btn-heal">
                {{ test.status === 'healed' ? '✓ Healed' : '🩺 Heal' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Healing Log -->
    <div class="section">
      <h3>Healing Log</h3>
      <div class="healing-log">
        <div v-for="entry in healingLog" :key="entry.id" class="log-entry">
          <span class="timestamp">{{ entry.timestamp }}</span>
          <span :class="['action', entry.action]">{{ entry.action }}</span>
          <span class="test-name">{{ entry.testName }}</span>
          <span class="details">{{ entry.details }}</span>
        </div>
      </div>
    </div>
    
    <!-- Detection Config -->
    <div class="section config-section">
      <h3>Detection Configuration</h3>
      <div class="config-grid">
        <div class="config-item">
          <label>Min Executions to Detect:</label>
          <input type="number" v-model="config.minExecutions" />
        </div>
        <div class="config-item">
          <label>Flakiness Threshold (%):</label>
          <input type="number" v-model="config.threshold" />
        </div>
        <div class="config-item">
          <label>Auto-Heal:</label>
          <input type="checkbox" v-model="config.autoHeal" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// State
const autoRefresh = ref(false)
const refreshInterval = ref(null)

const stats = ref({
  totalTests: 45,
  flakyTests: 8,
  healedTests: 5,
  healingRate: 62.5
})

const flakyTests = ref([
  { id: 1, name: 'test_login_flow', passRate: 70, executions: 10, avgDuration: 250, status: 'flaky' },
  { id: 2, name: 'test_user_create', passRate: 85, executions: 20, avgDuration: 180, status: 'stable' },
  { id: 3, name: 'test_profile_get', passRate: 60, executions: 15, avgDuration: 320, status: 'flaky' },
  { id: 4, name: 'test_post_delete', passRate: 95, executions: 8, avgDuration: 120, status: 'stable' },
  { id: 5, name: 'test_auth_refresh', passRate: 50, executions: 12, avgDuration: 400, status: 'flaky' },
])

const healingLog = ref([
  { id: 1, timestamp: '10:23:45', action: 'healed', testName: 'test_login_flow', details: 'Added 2s timeout' },
  { id: 2, timestamp: '10:22:30', action: 'detected', testName: 'test_profile_get', details: 'Flakiness detected: 60% pass rate' },
  { id: 3, timestamp: '10:20:15', action: 'healed', testName: 'test_post_create', details: 'Added retry logic' },
])

const config = ref({
  minExecutions: 5,
  threshold: 80,
  autoHeal: true
})

// Methods
function refreshStats() {
  // Simulated refresh
  console.log('Refreshing stats...')
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    refreshInterval.value = setInterval(refreshStats, 5000)
  } else {
    clearInterval(refreshInterval.value)
  }
}

function healTest(test) {
  test.status = 'healed'
  healingLog.value.unshift({
    id: Date.now(),
    timestamp: new Date().toLocaleTimeString(),
    action: 'healed',
    testName: test.name,
    details: 'Injected wait and retry logic'
  })
  stats.value.healedTests++
  stats.value.healingRate = Math.round((stats.value.healedTests / stats.value.flakyTests) * 100)
}

function getRowClass(test) {
  return {
    'row-flaky': test.status === 'flaky',
    'row-healed': test.status === 'healed',
    'row-stable': test.status === 'stable'
  }
}

function getStatusLabel(status) {
  const labels = {
    'flaky': 'Flaky',
    'stable': 'Stable',
    'healed': 'Healed'
  }
  return labels[status] || status
}

onMounted(() => {
  // Load initial stats
})

onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
})
</script>

<style scoped>
.flakiness-dashboard {
  padding: 20px;
  background: #1e1e1e;
  color: #d4d4d4;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dashboard-header h2 {
  margin: 0;
  color: #d4d4d4;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.btn-refresh, .btn-auto {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-refresh {
  background: #333;
  color: #d4d4d4;
}

.btn-auto {
  background: #333;
  color: #858585;
}

.btn-auto.active {
  background: #0e639c;
  color: white;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 30px;
}

.stat-card {
  background: #252526;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #3e3e42;
}

.stat-card.warning {
  border-color: #cca700;
}

.stat-card.success {
  border-color: #4ec9b0;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #d4d4d4;
}

.stat-label {
  font-size: 12px;
  color: #858585;
  margin-top: 5px;
}

.section {
  margin-bottom: 30px;
}

.section h3 {
  color: #d4d4d4;
  margin-bottom: 15px;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
}

.matrix-table th,
.matrix-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #3e3e42;
}

.matrix-table th {
  background: #252526;
  color: #858585;
  font-weight: 500;
}

.matrix-table tr.row-flaky {
  background: rgba(204, 167, 0, 0.1);
}

.matrix-table tr.row-healed {
  background: rgba(78, 201, 176, 0.1);
}

.test-name {
  font-family: monospace;
  color: #4ec9b0;
}

.pass-rate-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pass-rate-bar .fill {
  height: 8px;
  background: #4ec9b0;
  border-radius: 4px;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
}

.status-badge.flaky {
  background: #cca700;
  color: #000;
}

.status-badge.stable {
  background: #4ec9b0;
  color: #000;
}

.status-badge.healed {
  background: #569cd6;
  color: #fff;
}

.btn-heal {
  padding: 6px 12px;
  background: #0e639c;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-heal:disabled {
  background: #4ec9b0;
  cursor: default;
}

.healing-log {
  max-height: 200px;
  overflow-y: auto;
  background: #252526;
  border-radius: 8px;
  padding: 10px;
}

.log-entry {
  display: flex;
  gap: 15px;
  padding: 8px;
  border-bottom: 1px solid #3e3e42;
  font-size: 13px;
}

.log-entry .timestamp {
  color: #858585;
}

.log-entry .action {
  font-weight: bold;
}

.log-entry .action.healed {
  color: #4ec9b0;
}

.log-entry .action.detected {
  color: #cca700;
}

.config-section {
  background: #252526;
  padding: 20px;
  border-radius: 8px;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.config-item label {
  font-size: 12px;
  color: #858585;
}

.config-item input {
  padding: 8px;
  background: #333;
  border: 1px solid #3e3e42;
  border-radius: 4px;
  color: #d4d4d4;
}
</style>