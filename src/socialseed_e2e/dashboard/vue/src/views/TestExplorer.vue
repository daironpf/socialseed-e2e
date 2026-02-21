<template>
  <div class="test-explorer">
    <div class="explorer-header">
      <h2>Test Explorer</h2>
      <div class="search-box">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="Search tests..."
          class="search-input"
        />
      </div>
    </div>

    <div class="explorer-content">
      <div class="services-panel">
        <h3>Services</h3>
        <div class="services-list">
          <div 
            v-for="service in filteredServices" 
            :key="service.name"
            class="service-item"
            :class="{ active: selectedService === service.name }"
            @click="selectService(service.name)"
          >
            <span class="service-icon">📁</span>
            <span class="service-name">{{ service.name }}</span>
            <span class="service-count">{{ service.test_count }}</span>
          </div>
        </div>
      </div>

      <div class="tests-panel">
        <h3>Tests {{ selectedService ? `- ${selectedService}` : '- All' }}</h3>
        <div class="tests-list">
          <div 
            v-for="test in filteredTests" 
            :key="test.path"
            class="test-item"
            :class="{ active: selectedTest?.path === test.path }"
            @click="selectTest(test)"
          >
            <span class="test-icon">🧪</span>
            <div class="test-info">
              <span class="test-name">{{ test.name }}</span>
              <span class="test-path">{{ test.path }}</span>
            </div>
            <button class="run-btn" @click.stop="runSingleTest(test)">
              ▶️
            </button>
          </div>
          
          <div v-if="filteredTests.length === 0" class="empty-state">
            No tests found. Initialize a project with tests.
          </div>
        </div>
      </div>

      <div class="detail-panel" v-if="selectedTest">
        <h3>Test Details</h3>
        <div class="test-detail">
          <div class="detail-row">
            <span class="label">Name:</span>
            <span class="value">{{ selectedTest.name }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Path:</span>
            <span class="value">{{ selectedTest.path }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Service:</span>
            <span class="value">{{ selectedTest.service }}</span>
          </div>
          
          <div class="test-actions">
            <button class="btn btn-primary" @click="runSingleTest(selectedTest)">
              ▶️ Run Test
            </button>
            <button class="btn btn-secondary" @click="viewInEditor(selectedTest)">
              📝 Edit
            </button>
          </div>
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

const searchQuery = ref('')
const selectedService = ref(null)
const selectedTest = ref(null)

const filteredServices = computed(() => {
  if (!searchQuery.value) return testStore.services
  return testStore.services.filter(s => 
    s.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const filteredTests = computed(() => {
  let tests = testStore.tests
  
  if (selectedService.value) {
    tests = tests.filter(t => t.service === selectedService.value)
  }
  
  if (searchQuery.value) {
    tests = tests.filter(t => 
      t.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  
  return tests
})

const selectService = (service) => {
  selectedService.value = selectedService.value === service ? null : service
}

const selectTest = (test) => {
  selectedTest.value = test
}

const runSingleTest = async (test) => {
  logStore.addInfo(`Running test: ${test.name}`)
  try {
    await testStore.runTest(test.path)
    logStore.addSuccess(`Test ${test.name} completed`)
  } catch (error) {
    logStore.addError(`Test ${test.name} failed: ${error.message}`)
  }
}

const viewInEditor = (test) => {
  // Open in VS Code
  const { exec } = require('child_process')
  exec(`code ${test.path}`)
}
</script>

<style scoped>
.test-explorer {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.explorer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.explorer-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
}

.search-box {
  width: 300px;
}

.search-input {
  width: 100%;
  padding: 0.5rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 0.875rem;
}

.search-input:focus {
  outline: none;
  border-color: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.1);
}

.explorer-content {
  display: grid;
  grid-template-columns: 250px 1fr 300px;
  gap: 1.5rem;
  flex: 1;
  overflow: hidden;
}

.services-panel, .tests-panel, .detail-panel {
  background: white;
  border-radius: 0.75rem;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow-y: auto;
}

.services-panel h3, .tests-panel h3, .detail-panel h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 1rem;
}

.services-list, .tests-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.service-item, .test-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.service-item:hover, .test-item:hover {
  background: #f3f4f6;
}

.service-item.active, .test-item.active {
  background: #dcfce7;
  border: 1px solid #22c55e;
}

.service-icon, .test-icon {
  font-size: 1.25rem;
}

.service-name, .test-name {
  flex: 1;
  font-weight: 500;
}

.service-count {
  background: #e5e7eb;
  padding: 0.125rem 0.5rem;
  border-radius: 1rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.test-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.test-path {
  font-size: 0.75rem;
  color: #9ca3af;
}

.run-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
  border-radius: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.test-item:hover .run-btn {
  opacity: 1;
}

.run-btn:hover {
  background: #e5e7eb;
}

.test-detail {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-row .label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.detail-row .value {
  font-size: 0.875rem;
  color: #1f2937;
  word-break: break-all;
}

.test-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn {
  flex: 1;
  padding: 0.625rem 1rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #22c55e;
  color: white;
}

.btn-primary:hover {
  background: #16a34a;
}

.btn-secondary {
  background: #f3f4f6;
  color: #1f2937;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
}
</style>
