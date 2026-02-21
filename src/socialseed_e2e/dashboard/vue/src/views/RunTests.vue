<template>
  <div class="run-tests">
    <div class="run-header">
      <h2>Run Tests</h2>
      <div class="run-actions">
        <button 
          class="btn btn-primary btn-large" 
          @click="runAllTests"
          :disabled="testStore.isRunning"
        >
          <span v-if="testStore.isRunning" class="spinner">⏳</span>
          <span v-else>▶️</span>
          {{ testStore.isRunning ? 'Running...' : 'Run All Tests' }}
        </button>
      </div>
    </div>

    <div class="run-options">
      <div class="option-card">
        <h3>Service</h3>
        <select v-model="selectedService" class="select-input">
          <option value="">All Services</option>
          <option v-for="service in testStore.services" :key="service.name" :value="service.name">
            {{ service.name }} ({{ service.test_count }} tests)
          </option>
        </select>
      </div>

      <div class="option-card">
        <h3>Parameters</h3>
        <div class="params-input">
          <label>
            <span>Base URL</span>
            <input v-model="params.baseUrl" type="text" placeholder="http://localhost:8000" />
          </label>
          <label>
            <span>Timeout (ms)</span>
            <input v-model="params.timeout" type="number" placeholder="30000" />
          </label>
          <label>
            <span>Custom Variables (JSON)</span>
            <textarea v-model="params.variables" placeholder='{"key": "value"}' rows="3"></textarea>
          </label>
        </div>
      </div>
    </div>

    <div class="progress-section" v-if="testStore.isRunning">
      <div class="progress-header">
        <span>Running Tests</span>
        <span class="progress-percent">{{ testStore.runProgress }}%</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: testStore.runProgress + '%' }"></div>
      </div>
      <div class="progress-details">
        {{ currentTest }}
      </div>
    </div>

    <div class="results-section">
      <h3>Results</h3>
      <div class="results-summary">
        <div class="summary-card passed">
          <span class="summary-icon">✅</span>
          <span class="summary-value">{{ passedCount }}</span>
          <span class="summary-label">Passed</span>
        </div>
        <div class="summary-card failed">
          <span class="summary-icon">❌</span>
          <span class="summary-value">{{ failedCount }}</span>
          <span class="summary-label">Failed</span>
        </div>
        <div class="summary-card total">
          <span class="summary-icon">📊</span>
          <span class="summary-value">{{ totalCount }}</span>
          <span class="summary-label">Total</span>
        </div>
        <div class="summary-card duration">
          <span class="summary-icon">⏱️</span>
          <span class="summary-value">{{ totalDuration }}ms</span>
          <span class="summary-label">Duration</span>
        </div>
      </div>

      <div class="results-list">
        <div 
          v-for="result in testStore.testResults" 
          :key="result.id"
          class="result-item"
          :class="result.status"
        >
          <span class="result-status">
            {{ result.status === 'passed' ? '✅' : result.status === 'failed' ? '❌' : '⏳' }}
          </span>
          <div class="result-info">
            <span class="result-name">{{ result.test_name || result.test }}</span>
            <span class="result-path">{{ result.test_path }}</span>
          </div>
          <div class="result-meta">
            <span class="result-duration" v-if="result.duration">{{ result.duration }}ms</span>
            <span class="result-time">{{ formatTime(result.timestamp || result.created_at) }}</span>
          </div>
          <div class="result-error" v-if="result.error">
            {{ result.error }}
          </div>
        </div>

        <div v-if="testStore.testResults.length === 0" class="empty-state">
          No results yet. Run tests to see results here.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTestStore } from '../stores/testStore'
import { useLogStore } from '../stores/logStore'

const testStore = useTestStore()
const logStore = useLogStore()

const selectedService = ref('')
const params = ref({
  baseUrl: 'http://localhost:8000',
  timeout: 30000,
  variables: '{}'
})

const currentTest = computed(() => {
  return testStore.testResults[0]?.test_name || 'Preparing...'
})

const passedCount = computed(() => testStore.testResults.filter(r => r.status === 'passed').length)
const failedCount = computed(() => testStore.testResults.filter(r => r.status === 'failed').length)
const totalCount = computed(() => testStore.testResults.length)
const totalDuration = computed(() => testStore.testResults.reduce((sum, r) => sum + (r.duration || 0), 0))

const runAllTests = async () => {
  logStore.addInfo('Starting test run...')
  try {
    await testStore.runAllTests(selectedService.value || null)
    logStore.addSuccess('Test run completed')
  } catch (error) {
    logStore.addError(`Test run failed: ${error.message}`)
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleTimeString()
}
</script>

<style scoped>
.run-tests {
  max-width: 1200px;
  margin: 0 auto;
}

.run-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.run-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
}

.btn {
  padding: 0.625rem 1rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background: #22c55e;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #16a34a;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-large {
  padding: 0.875rem 1.5rem;
  font-size: 1rem;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.run-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.option-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.option-card h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 1rem;
}

.select-input, .params-input input, .params-input textarea {
  width: 100%;
  padding: 0.625rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 0.875rem;
}

.select-input:focus, .params-input input:focus, .params-input textarea:focus {
  outline: none;
  border-color: #22c55e;
}

.params-input label {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.params-input label span {
  font-size: 0.75rem;
  color: #6b7280;
}

.progress-section {
  background: white;
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  font-weight: 500;
}

.progress-percent {
  color: #22c55e;
}

.progress-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #22c55e, #4ade80);
  transition: width 0.3s ease;
}

.progress-details {
  margin-top: 0.75rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.results-section {
  background: white;
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.results-section h3 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.results-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.summary-card {
  background: #f9fafb;
  border-radius: 0.5rem;
  padding: 1rem;
  text-align: center;
}

.summary-card.passed { background: #dcfce7; }
.summary-card.failed { background: #fee2e2; }

.summary-icon {
  font-size: 1.5rem;
  display: block;
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  display: block;
}

.summary-label {
  font-size: 0.75rem;
  color: #6b7280;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.result-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 0.5rem;
  border-left: 3px solid #e5e7eb;
}

.result-item.passed { border-left-color: #22c55e; }
.result-item.failed { border-left-color: #ef4444; }

.result-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.result-name {
  font-weight: 500;
}

.result-path {
  font-size: 0.75rem;
  color: #9ca3af;
}

.result-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.result-error {
  width: 100%;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #fee2e2;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  color: #dc2626;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
}
</style>
