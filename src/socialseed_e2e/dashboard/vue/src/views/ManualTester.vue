<template>
  <div class="manual-tester-container">
    <!-- T04: Manual Tester - Ejecutar Suites y ver Logs -->
    
    <div class="tester-layout">
      <!-- Left Panel: Test Suites -->
      <div class="suites-panel">
        <h3>Test Suites</h3>
        
        <div class="suite-list">
          <div 
            v-for="suite in testSuites" 
            :key="suite.id"
            class="suite-item"
            :class="{ selected: selectedSuite?.id === suite.id, running: suite.running }"
            @click="selectSuite(suite)"
          >
            <div class="suite-info">
              <span class="suite-name">{{ suite.name }}</span>
              <span class="suite-status">{{ suite.status }}</span>
            </div>
            <div class="suite-stats">
              <span class="stat">{{ suite.tests }} tests</span>
              <span class="stat pass">{{ suite.passed }} passed</span>
              <span class="stat fail">{{ suite.failed }} failed</span>
            </div>
          </div>
        </div>
        
        <div class="actions">
          <button @click="runSelectedSuite" class="btn-run" :disabled="!selectedSuite || isRunning">
            {{ isRunning ? '⏳ Running...' : '▶ Run Suite' }}
          </button>
          <button @click="runAllSuites" class="btn-run-all" :disabled="isRunning">
            Run All
          </button>
        </div>
      </div>
      
      <!-- Right Panel: Test Results & Logs -->
      <div class="results-panel">
        <!-- Test Progress -->
        <div v-if="isRunning" class="progress-section">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <div class="progress-info">
            <span>{{ currentTest }}</span>
            <span>{{ passedTests }}/{{ totalTests }} passed</span>
          </div>
        </div>
        
        <!-- Results Table -->
        <div class="results-table">
          <table>
            <thead>
              <tr>
                <th>Status</th>
                <th>Test Name</th>
                <th>Duration</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="test in testResults" 
                :key="test.id"
                :class="{ passed: test.status === 'passed', failed: test.status === 'failed' }"
              >
                <td>
                  <span :class="['status-icon', test.status]">
                    {{ test.status === 'passed' ? '✓' : '✗' }}
                  </span>
                </td>
                <td>{{ test.name }}</td>
                <td>{{ test.duration }}ms</td>
                <td>{{ test.message || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- Visual Logs -->
        <div class="logs-section">
          <div class="logs-header">
            <h4>Execution Logs</h4>
            <div class="log-controls">
              <button @click="toggleAutoScroll" :class="{ active: autoScroll }">
                Auto-scroll
              </button>
              <button @click="clearLogs">Clear</button>
            </div>
          </div>
          <div ref="logContainer" class="log-output">
            <div 
              v-for="(log, index) in logs" 
              :key="index"
              :class="['log-entry', log.level]"
            >
              <span class="log-time">{{ log.timestamp }}</span>
              <span :class="['log-level', log.level]">{{ log.level.toUpperCase() }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'

// State
const testSuites = ref([
  { id: 1, name: 'Auth Flow Tests', status: 'ready', tests: 5, passed: 0, failed: 0, running: false },
  { id: 2, name: 'User CRUD Tests', status: 'ready', tests: 8, passed: 0, failed: 0, running: false },
  { id: 3, name: 'Security Tests', status: 'ready', tests: 12, passed: 0, failed: 0, running: false },
])

const selectedSuite = ref(null)
const isRunning = ref(false)
const progressPercent = ref(0)
const currentTest = ref('')
const passedTests = ref(0)
const totalTests = ref(0)
const testResults = ref([])
const logs = ref([])
const autoScroll = ref(true)
const logContainer = ref(null)

// Methods
function selectSuite(suite) {
  selectedSuite.value = suite
}

async function runSelectedSuite() {
  if (!selectedSuite.value) return
  
  isRunning.value = true
  selectedSuite.value.running = true
  progressPercent.value = 0
  testResults.value = []
  logs.value = []
  passedTests.value = 0
  totalTests.value = selectedSuite.value.tests
  
  // Simulate test execution
  for (let i = 1; i <= selectedSuite.value.tests; i++) {
    currentTest.value = `Test ${i}/${selectedSuite.value.tests}`
    
    // Add log entry
    addLog('info', `Running test ${i}...`)
    
    // Simulate test execution
    await simulateTestExecution()
    
    progressPercent.value = (i / totalTests.value) * 100
  }
  
  selectedSuite.value.status = 'completed'
  selectedSuite.value.running = false
  isRunning.value = false
  currentTest.value = ''
  
  addLog('info', 'Test suite completed')
}

async function runAllSuites() {
  for (const suite of testSuites.value) {
    selectedSuite.value = suite
    await runSelectedSuite()
  }
}

async function simulateTestExecution() {
  // Simulate async test
  await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 500))
  
  // Random pass/fail (80% pass rate)
  const passed = Math.random() > 0.2
  
  if (passed) {
    passedTests.value++
    testResults.value.push({
      id: Date.now(),
      name: currentTest.value,
      status: 'passed',
      duration: Math.floor(Math.random() * 200) + 50,
      message: ''
    })
    addLog('pass', `✓ Test passed`)
  } else {
    testResults.value.push({
      id: Date.now(),
      name: currentTest.value,
      status: 'failed',
      duration: Math.floor(Math.random() * 200) + 50,
      message: 'Assertion failed: expected 200, got 500'
    })
    addLog('fail', `✗ Test failed: Assertion error`)
  }
}

function addLog(level, message) {
  logs.value.push({
    timestamp: new Date().toLocaleTimeString(),
    level,
    message
  })
  
  // Auto-scroll if enabled
  if (autoScroll.value && logContainer.value) {
    nextTick(() => {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    })
  }
}

function toggleAutoScroll() {
  autoScroll.value = !autoScroll.value
}

function clearLogs() {
  logs.value = []
}
</script>

<style scoped>
.manual-tester-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
}

.tester-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.suites-panel {
  width: 280px;
  background: #252526;
  border-right: 1px solid #3e3e42;
  display: flex;
  flex-direction: column;
}

.suites-panel h3 {
  padding: 15px;
  margin: 0;
  color: #d4d4d4;
  border-bottom: 1px solid #3e3e42;
}

.suite-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.suite-item {
  padding: 12px;
  margin-bottom: 8px;
  background: #2d2d2d;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid transparent;
}

.suite-item:hover {
  background: #333;
}

.suite-item.selected {
  border-color: #0e639c;
}

.suite-item.running {
  border-color: #cca700;
}

.suite-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.suite-name {
  color: #d4d4d4;
  font-weight: 500;
}

.suite-status {
  color: #858585;
  font-size: 11px;
}

.suite-stats {
  display: flex;
  gap: 10px;
  font-size: 11px;
}

.stat.pass { color: #4ec9b0; }
.stat.fail { color: #f14c4c; }

.actions {
  padding: 15px;
  border-top: 1px solid #3e3e42;
  display: flex;
  gap: 10px;
}

.btn-run, .btn-run-all {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-run {
  background: #0e639c;
  color: white;
}

.btn-run:disabled {
  background: #3c3c3c;
  color: #858585;
}

.btn-run-all {
  background: #3c3c3c;
  color: #d4d4d4;
}

.results-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.progress-section {
  padding: 15px;
  background: #252526;
  border-bottom: 1px solid #3e3e42;
}

.progress-bar {
  height: 8px;
  background: #3c3c3c;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: #0e639c;
  transition: width 0.3s;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  color: #858585;
  font-size: 12px;
}

.results-table {
  flex: 1;
  overflow: auto;
}

.results-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.results-table th {
  text-align: left;
  padding: 10px;
  background: #2d2d2d;
  color: #858585;
}

.results-table td {
  padding: 8px 10px;
  border-bottom: 1px solid #2d2d2d;
}

.results-table tr.passed {
  background: rgba(78, 201, 176, 0.1);
}

.results-table tr.failed {
  background: rgba(241, 76, 76, 0.1);
}

.status-icon {
  font-weight: bold;
}

.status-icon.passed { color: #4ec9b0; }
.status-icon.failed { color: #f14c4c; }

.logs-section {
  height: 250px;
  background: #1e1e1e;
  border-top: 1px solid #3e3e42;
  display: flex;
  flex-direction: column;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  padding: 10px 15px;
  background: #252526;
  border-bottom: 1px solid #3e3e42;
}

.logs-header h4 {
  margin: 0;
  color: #d4d4d4;
}

.log-controls {
  display: flex;
  gap: 10px;
}

.log-controls button {
  padding: 4px 10px;
  background: #3c3c3c;
  border: none;
  color: #858585;
  border-radius: 3px;
  cursor: pointer;
  font-size: 11px;
}

.log-controls button.active {
  background: #0e639c;
  color: white;
}

.log-output {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  font-family: 'Consolas', monospace;
  font-size: 12px;
}

.log-entry {
  padding: 2px 0;
}

.log-time {
  color: #858585;
  margin-right: 10px;
}

.log-level {
  margin-right: 10px;
  font-weight: bold;
}

.log-level.info { color: #569cd6; }
.log-level.pass { color: #4ec9b0; }
.log-level.fail { color: #f14c4c; }
.log-level.warn { color: #cca700; }

.log-message {
  color: #d4d4d4;
}
</style>