<template>
  <div class="dashboard">
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">🧪</div>
        <div class="stat-content">
          <div class="stat-value">{{ totalTests }}</div>
          <div class="stat-label">Total Tests</div>
        </div>
      </div>
      
      <div class="stat-card success">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ passedCount }}</div>
          <div class="stat-label">Passed</div>
        </div>
      </div>
      
      <div class="stat-card error">
        <div class="stat-icon">❌</div>
        <div class="stat-content">
          <div class="stat-value">{{ failedCount }}</div>
          <div class="stat-label">Failed</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">⏱️</div>
        <div class="stat-content">
          <div class="stat-value">{{ totalDuration }}ms</div>
          <div class="stat-label">Total Duration</div>
        </div>
      </div>
    </div>

    <div class="dashboard-grid">
      <div class="card recent-runs">
        <h3>Recent Test Runs</h3>
        <div class="runs-list">
          <div 
            v-for="result in recentResults" 
            :key="result.id" 
            class="run-item"
            :class="result.status"
          >
            <span class="run-status">{{ result.status === 'passed' ? '✅' : '❌' }}</span>
            <span class="run-name">{{ result.test_name }}</span>
            <span class="run-duration">{{ result.duration }}ms</span>
          </div>
          <div v-if="recentResults.length === 0" class="empty-state">
            No test runs yet. Run some tests to see results here.
          </div>
        </div>
      </div>

      <div class="card services-overview">
        <h3>Services Overview</h3>
        <div class="services-list">
          <div 
            v-for="service in services" 
            :key="service.name" 
            class="service-item"
          >
            <span class="service-name">{{ service.name }}</span>
            <span class="service-count">{{ service.test_count }} tests</span>
          </div>
          <div v-if="services.length === 0" class="empty-state">
            No services found. Initialize a project to see services.
          </div>
        </div>
      </div>

      <div class="card quick-actions">
        <h3>Quick Actions</h3>
        <div class="actions-grid">
          <button class="action-btn" @click="$router.push('/run')">
            <span class="action-icon">▶️</span>
            <span>Run All Tests</span>
          </button>
          <button class="action-btn" @click="$router.push('/tests')">
            <span class="action-icon">🔍</span>
            <span>Explore Tests</span>
          </button>
          <button class="action-btn" @click="$router.push('/history')">
            <span class="action-icon">📜</span>
            <span>View History</span>
          </button>
          <button class="action-btn" @click="$router.push('/settings')">
            <span class="action-icon">⚙️</span>
            <span>Settings</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useTestStore } from '../stores/testStore'

const testStore = useTestStore()

const totalTests = computed(() => testStore.tests.length)
const passedCount = computed(() => testStore.passedCount)
const failedCount = computed(() => testStore.failedCount)
const totalDuration = computed(() => testStore.totalDuration)
const services = computed(() => testStore.services)
const recentResults = computed(() => testStore.testResults.slice(0, 10))
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stat-icon {
  font-size: 2rem;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1f2937;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
}

.stat-card.success .stat-value {
  color: #22c55e;
}

.stat-card.error .stat-value {
  color: #ef4444;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
}

.card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.card h3 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
}

.runs-list, .services-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.run-item, .service-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 0.5rem;
}

.run-name, .service-name {
  flex: 1;
  font-weight: 500;
}

.run-duration {
  font-size: 0.875rem;
  color: #6b7280;
}

.service-count {
  font-size: 0.875rem;
  color: #6b7280;
  background: #e5e7eb;
  padding: 0.25rem 0.5rem;
  border-radius: 1rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: #f3f4f6;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #e5e7eb;
  transform: translateY(-1px);
}

.action-icon {
  font-size: 1.25rem;
}
</style>
