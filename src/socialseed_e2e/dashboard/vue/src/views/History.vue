<template>
  <div class="history">
    <div class="history-header">
      <h2>Test History</h2>
      <div class="filters">
        <select v-model="statusFilter" class="filter-select">
          <option value="">All Status</option>
          <option value="passed">Passed</option>
          <option value="failed">Failed</option>
        </select>
        <select v-model="serviceFilter" class="filter-select">
          <option value="">All Services</option>
          <option v-for="service in services" :key="service" :value="service">
            {{ service }}
          </option>
        </select>
      </div>
    </div>

    <div class="history-table-wrapper">
      <table class="history-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Test Name</th>
            <th>Service</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="result in filteredResults" :key="result.id">
            <td class="date-cell">{{ formatDate(result.timestamp) }}</td>
            <td class="name-cell">{{ result.test_name }}</td>
            <td>
              <span class="service-badge">{{ result.service || 'N/A' }}</span>
            </td>
            <td>
              <span :class="['status-badge', result.status]">
                {{ result.status }}
              </span>
            </td>
            <td class="duration-cell">{{ result.duration }}ms</td>
            <td class="actions-cell">
              <button class="icon-btn" @click="viewDetails(result)" title="View Details">
                👁️
              </button>
              <button class="icon-btn" @click="rerunTest(result)" title="Re-run">
                🔄
              </button>
              <button class="icon-btn" @click="deleteResult(result.id)" title="Delete">
                🗑️
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div v-if="filteredResults.length === 0" class="empty-state">
        No test history found matching your filters.
      </div>
    </div>

    <div v-if="selectedResult" class="modal-overlay" @click.self="selectedResult = null">
      <div class="modal">
        <div class="modal-header">
          <h3>Test Details</h3>
          <button class="close-btn" @click="selectedResult = null">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-row">
            <span class="detail-label">Test Name:</span>
            <span class="detail-value">{{ selectedResult.test_name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Status:</span>
            <span :class="['status-badge', selectedResult.status]">{{ selectedResult.status }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Duration:</span>
            <span class="detail-value">{{ selectedResult.duration }}ms</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Timestamp:</span>
            <span class="detail-value">{{ formatDate(selectedResult.timestamp) }}</span>
          </div>
          <div v-if="selectedResult.error" class="detail-section">
            <span class="detail-label">Error:</span>
            <pre class="error-output">{{ selectedResult.error }}</pre>
          </div>
          <div v-if="selectedResult.response" class="detail-section">
            <span class="detail-label">Response:</span>
            <pre class="response-output">{{ formatJson(selectedResult.response) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTestStore } from '../stores/testStore'
import { useRouter } from 'vue-router'

const testStore = useTestStore()
const router = useRouter()

const statusFilter = ref('')
const serviceFilter = ref('')
const selectedResult = ref(null)

const services = computed(() => {
  const serviceSet = new Set(testStore.testResults.map(r => r.service).filter(Boolean))
  return Array.from(serviceSet)
})

const filteredResults = computed(() => {
  return testStore.testResults.filter(result => {
    if (statusFilter.value && result.status !== statusFilter.value) return false
    if (serviceFilter.value && result.service !== serviceFilter.value) return false
    return true
  })
})

const formatDate = (timestamp) => {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp)
  return date.toLocaleString()
}

const formatJson = (data) => {
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return data
  }
}

const viewDetails = (result) => {
  selectedResult.value = result
}

const rerunTest = (result) => {
  router.push({ path: '/run', query: { test: result.test_name } })
}

const deleteResult = (id) => {
  testStore.deleteResult(id)
}
</script>

<style scoped>
.history {
  max-width: 1400px;
  margin: 0 auto;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.history-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #1f2937;
}

.filters {
  display: flex;
  gap: 1rem;
}

.filter-select {
  padding: 0.5rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: white;
  font-size: 0.875rem;
}

.history-table-wrapper {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th,
.history-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.history-table th {
  background: #f9fafb;
  font-weight: 600;
  color: #6b7280;
  font-size: 0.875rem;
  text-transform: uppercase;
}

.date-cell {
  white-space: nowrap;
  color: #6b7280;
}

.name-cell {
  font-weight: 500;
}

.service-badge {
  background: #e0e7ff;
  color: #4338ca;
  padding: 0.25rem 0.5rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.status-badge.passed {
  background: #dcfce7;
  color: #166534;
}

.status-badge.failed {
  background: #fee2e2;
  color: #991b1b;
}

.duration-cell {
  font-family: monospace;
}

.actions-cell {
  display: flex;
  gap: 0.5rem;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  font-size: 1rem;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.icon-btn:hover {
  opacity: 1;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #9ca3af;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: white;
  border-radius: 0.75rem;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
}

.modal-body {
  padding: 1.5rem;
}

.detail-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.detail-label {
  font-weight: 500;
  color: #6b7280;
  min-width: 100px;
}

.detail-value {
  color: #1f2937;
}

.detail-section {
  margin-top: 1rem;
}

.error-output,
.response-output {
  background: #1f2937;
  color: #e5e7eb;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}
</style>
