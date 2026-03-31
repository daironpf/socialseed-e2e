<template>
  <div class="live-traffic-container">
    <!-- T03: Tabla interactiva Live Traffic similar a Chrome Network Tab -->
    
    <!-- Controls -->
    <div class="controls">
      <div class="search-box">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="Filter requests..."
          @input="filterRequests"
        />
      </div>
      <div class="buttons">
        <button @click="clearRequests" class="btn-clear">Clear</button>
        <button @click="toggleRecording" :class="['btn-record', { recording: isRecording }]">
          {{ isRecording ? '⏹ Stop' : '⏺ Record' }}
        </button>
      </div>
    </div>
    
    <!-- Statistics -->
    <div class="stats">
      <span class="stat">
        <span class="label">Requests:</span>
        <span class="value">{{ requests.length }}</span>
      </span>
      <span class="stat">
        <span class="label">Errors:</span>
        <span class="value error">{{ errorCount }}</span>
      </span>
      <span class="stat">
        <span class="label">Avg:</span>
        <span class="value">{{ avgDuration }}ms</span>
      </span>
    </div>
    
    <!-- Network Table -->
    <div class="network-table">
      <table>
        <thead>
          <tr>
            <th class="col-status">Status</th>
            <th class="col-method">Method</th>
            <th class="col-name">Name</th>
            <th class="col-type">Type</th>
            <th class="col-initiator">Initiator</th>
            <th class="col-size">Size</th>
            <th class="col-time">Time</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="req in filteredRequests" 
            :key="req.id"
            @click="selectRequest(req)"
            :class="{ selected: selectedRequest?.id === req.id, error: req.status >= 400 }"
          >
            <td class="col-status">
              <span :class="['status', getStatusClass(req.status)]">{{ req.status }}</span>
            </td>
            <td class="col-method">
              <span :class="['method', req.method.toLowerCase()]">{{ req.method }}</span>
            </td>
            <td class="col-name">{{ req.name }}</td>
            <td class="col-type">{{ req.type || 'fetch' }}</td>
            <td class="col-initiator">{{ req.initiator || '-' }}</td>
            <td class="col-size">{{ req.size || '-' }}</td>
            <td class="col-time">{{ req.duration }}ms</td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Request Details Panel -->
    <div v-if="selectedRequest" class="request-details">
      <div class="details-header">
        <h3>{{ selectedRequest.name }}</h3>
        <button @click="selectedRequest = null" class="btn-close">×</button>
      </div>
      <div class="details-tabs">
        <button 
          :class="{ active: activeTab === 'headers' }" 
          @click="activeTab = 'headers'"
        >Headers</button>
        <button 
          :class="{ active: activeTab === 'payload' }" 
          @click="activeTab = 'payload'"
        >Payload</button>
        <button 
          :class="{ active: activeTab === 'response' }" 
          @click="activeTab = 'response'"
        >Response</button>
      </div>
      <div class="details-content">
        <!-- Headers Tab -->
        <div v-if="activeTab === 'headers'" class="tab-content">
          <h4>Request Headers</h4>
          <pre>{{ formatJSON(selectedRequest.requestHeaders) }}</pre>
          <h4>Response Headers</h4>
          <pre>{{ formatJSON(selectedRequest.responseHeaders) }}</pre>
        </div>
        
        <!-- Payload Tab -->
        <div v-if="activeTab === 'payload'" class="tab-content">
          <pre>{{ selectedRequest.requestBody || 'No body' }}</pre>
        </div>
        
        <!-- Response Tab -->
        <div v-if="activeTab === 'response'" class="tab-content">
          <pre>{{ selectedRequest.responseBody || 'No response' }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

// State
const searchQuery = ref('')
const isRecording = ref(true)
const requests = ref([])
const selectedRequest = ref(null)
const activeTab = ref('headers')
let ws = null

// Computed
const filteredRequests = computed(() => {
  if (!searchQuery.value) return requests.value
  const query = searchQuery.value.toLowerCase()
  return requests.value.filter(req => 
    req.name.toLowerCase().includes(query) ||
    req.method.toLowerCase().includes(query)
  )
})

const errorCount = computed(() => 
  requests.value.filter(r => r.status >= 400).length
)

const avgDuration = computed(() => {
  if (requests.value.length === 0) return 0
  const total = requests.value.reduce((sum, r) => sum + r.duration, 0)
  return Math.round(total / requests.value.length)
})

// Methods
function filterRequests() {
  // Filtering is handled by computed property
}

function clearRequests() {
  requests.value = []
  selectedRequest.value = null
}

function toggleRecording() {
  isRecording.value = !isRecording.value
}

function selectRequest(req) {
  selectedRequest.value = req
}

function getStatusClass(status) {
  if (status >= 500) return 'status-error'
  if (status >= 400) return 'status-warning'
  if (status >= 300) return 'status-redirect'
  return 'status-success'
}

function formatJSON(obj) {
  if (!obj) return '{}'
  return typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2)
}

// WebSocket connection for real-time updates
function connectWebSocket() {
  // Connect to WebSocket bridge
  const wsUrl = 'ws://localhost:8000/ws/traffic'
  
  try {
    ws = new WebSocket(wsUrl)
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'traffic' && isRecording.value) {
        requests.value.unshift({
          id: Date.now(),
          ...data.data,
          timestamp: new Date()
        })
        
        // Keep only last 100 requests
        if (requests.value.length > 100) {
          requests.value.pop()
        }
      }
    }
    
    ws.onerror = (error) => {
      console.log('WebSocket error (dashboard may not be running):', error)
    }
  } catch (e) {
    console.log('WebSocket not available')
  }
}

// Lifecycle
onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.live-traffic-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  color: #d4d4d4;
}

.controls {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: #252526;
  border-bottom: 1px solid #3e3e42;
}

.search-box input {
  background: #3c3c3c;
  border: 1px solid #3e3e42;
  color: #d4d4d4;
  padding: 5px 10px;
  border-radius: 4px;
  width: 300px;
}

.buttons {
  display: flex;
  gap: 10px;
}

.btn-clear, .btn-record {
  padding: 5px 15px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-clear {
  background: #3c3c3c;
  color: #d4d4d4;
}

.btn-record {
  background: #0e639c;
  color: white;
}

.btn-record.recording {
  background: #c53030;
}

.stats {
  display: flex;
  gap: 20px;
  padding: 10px;
  background: #252526;
  font-size: 12px;
}

.stat .label {
  color: #858585;
}

.stat .value.error {
  color: #f14c4c;
}

.network-table {
  flex: 1;
  overflow: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

th {
  text-align: left;
  padding: 8px;
  background: #2d2d2d;
  color: #858585;
  position: sticky;
  top: 0;
}

td {
  padding: 6px 8px;
  border-bottom: 1px solid #2d2d2d;
  cursor: pointer;
}

tr:hover {
  background: #2a2d2e;
}

tr.selected {
  background: #094771;
}

.method {
  font-weight: bold;
}

.method.get { color: #4ec9b0; }
.method.post { color: #ce9178; }
.method.put { color: #dcdcaa; }
.method.delete { color: #f14c4c; }
.method.patch { color: #c586c0; }

.status-success { color: #4ec9b0; }
.status-warning { color: #cca700; }
.status-error { color: #f14c4c; }
.status-redirect { color: #569cd6; }

.request-details {
  height: 300px;
  background: #1e1e1e;
  border-top: 1px solid #3e3e42;
  display: flex;
  flex-direction: column;
}

.details-header {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: #252526;
}

.details-tabs {
  display: flex;
  gap: 5px;
  padding: 5px 10px;
  background: #252526;
}

.details-tabs button {
  background: transparent;
  border: none;
  color: #858585;
  padding: 5px 10px;
  cursor: pointer;
}

.details-tabs button.active {
  color: #d4d4d4;
  border-bottom: 2px solid #0e639c;
}

.details-content {
  flex: 1;
  overflow: auto;
  padding: 10px;
}

.tab-content pre {
  background: #1e1e1e;
  color: #9cdcfe;
  padding: 10px;
  font-size: 11px;
  white-space: pre-wrap;
}
</style>