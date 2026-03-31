<template>
  <div class="topology-container">
    <div class="topology-header">
      <h2>Microservices Dependency Graph</h2>
      <div class="controls">
        <button @click="refreshTopology" class="btn-refresh">🔄 Refresh</button>
        <button @click="resetGraph" class="btn-reset">Reset</button>
        <button @click="toggleAutoRefresh" :class="['btn-auto', { active: autoRefresh }]">
          {{ autoRefresh ? '⏸ Auto' : '▶ Auto' }}
        </button>
      </div>
    </div>

    <!-- Health Summary -->
    <div class="health-summary">
      <div class="health-card" :class="healthSummary.overall_health">
        <span class="health-label">Overall Health</span>
        <span class="health-value">{{ healthSummary.overall_health }}</span>
      </div>
      <div class="health-stat">
        <span class="stat-label">Services</span>
        <span class="stat-value">{{ healthSummary.nodes?.total || 0 }}</span>
      </div>
      <div class="health-stat healthy">
        <span class="stat-label">Healthy</span>
        <span class="stat-value">{{ healthSummary.nodes?.healthy || 0 }}</span>
      </div>
      <div class="health-stat error">
        <span class="stat-label">Errors</span>
        <span class="stat-value">{{ healthSummary.nodes?.error || 0 }}</span>
      </div>
      <div class="health-stat">
        <span class="stat-label">Connections</span>
        <span class="stat-value">{{ healthSummary.links?.total || 0 }}</span>
      </div>
    </div>

    <!-- Graph Container -->
    <div class="graph-container" ref="graphContainer">
      <svg ref="svgGraph" class="topology-svg"></svg>
      
      <!-- Legend -->
      <div class="legend">
        <div class="legend-item">
          <span class="legend-dot healthy"></span>
          <span>Healthy</span>
        </div>
        <div class="legend-item">
          <span class="legend-dot slow"></span>
          <span>Slow</span>
        </div>
        <div class="legend-item">
          <span class="legend-dot error"></span>
          <span>Error</span>
        </div>
      </div>

      <!-- Node Details Panel -->
      <div v-if="selectedNode" class="node-details">
        <div class="details-header">
          <h3>{{ selectedNode.id }}</h3>
          <button @click="selectedNode = null" class="btn-close">×</button>
        </div>
        <div class="details-body">
          <div class="detail-row">
            <span class="label">Status:</span>
            <span :class="['value', selectedNode.status]">{{ selectedNode.status }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Total Requests:</span>
            <span class="value">{{ selectedNode.requests }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Avg Duration:</span>
            <span class="value">{{ selectedNode.avgDuration }}ms</span>
          </div>
          <div class="detail-row">
            <span class="label">Endpoints:</span>
            <ul class="endpoints-list">
              <li v-for="ep in selectedNode.endpoints" :key="ep">{{ ep }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Connection Details -->
    <div v-if="selectedConnection" class="connection-details">
      <div class="details-header">
        <h3>{{ selectedConnection.source }} → {{ selectedConnection.target }}</h3>
        <button @click="selectedConnection = null" class="btn-close">×</button>
      </div>
      <div class="details-body">
        <div class="detail-row">
          <span class="label">Status:</span>
          <span :class="['value', selectedConnection.status]">{{ selectedConnection.status }}</span>
        </div>
        <div class="detail-row">
          <span class="label">Request Count:</span>
          <span class="value">{{ selectedConnection.requests }}</span>
        </div>
        <div class="detail-row">
          <span class="label">Avg Duration:</span>
          <span class="value">{{ selectedConnection.avgDuration }}ms</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useWebSocket } from '@vueuse/core'

const props = defineProps({
  wsUrl: {
    type: String,
    default: 'ws://localhost:8765'
  }
})

const graphContainer = ref(null)
const svgGraph = ref(null)

const topology = ref({ nodes: [], links: [] })
const selectedNode = ref(null)
const selectedConnection = ref(null)
const autoRefresh = ref(true)

const healthSummary = computed(() => {
  const nodes = topology.value.nodes || []
  const links = topology.value.links || []
  
  const healthyNodes = nodes.filter(n => n.status === 'healthy').length
  const errorNodes = nodes.filter(n => n.status === 'error').length
  const totalNodes = nodes.length
  
  return {
    nodes: {
      total: totalNodes,
      healthy: healthyNodes,
      error: errorNodes
    },
    links: {
      total: links.length,
      ok: links.filter(l => l.status === 'ok').length,
      error: links.filter(l => l.status === 'error').length
    },
    overall_health: errorNodes === 0 ? 'healthy' : errorNodes <= totalNodes / 3 ? 'degraded' : 'critical'
  }
})

let ws = null
let refreshInterval = null

const connectWebSocket = () => {
  try {
    ws = new WebSocket(`${props.wsUrl}/topology`)
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        topology.value = data
      } catch (e) {
        console.error('Failed to parse topology data:', e)
      }
    }
    
    ws.onerror = () => {
      console.log('WebSocket not available, using polling')
      startPolling()
    }
  } catch (e) {
    startPolling()
  }
}

const startPolling = () => {
  if (refreshInterval) return
  
  refreshInterval = setInterval(() => {
    if (autoRefresh.value) {
      fetchTopology()
    }
  }, 3000)
}

const fetchTopology = async () => {
  try {
    const response = await fetch('/api/topology')
    if (response.ok) {
      topology.value = await response.json()
    }
  } catch (e) {
    console.log('Using demo topology data')
  }
}

const refreshTopology = () => {
  fetchTopology()
}

const resetGraph = () => {
  topology.value = { nodes: [], links: [] }
  selectedNode.value = null
  selectedConnection.value = null
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
}

const renderGraph = () => {
  if (!svgGraph.value || !topology.value.nodes.length) return
  
  const svg = svgGraph.value
  const width = graphContainer.value?.clientWidth || 800
  const height = graphContainer.value?.clientHeight || 500
  
  svg.setAttribute('width', width)
  svg.setAttribute('height', height)
  svg.innerHTML = ''
  
  const nodes = topology.value.nodes
  const links = topology.value.links
  
  const centerX = width / 2
  const centerY = height / 2
  const radius = Math.min(width, height) / 3
  
  const nodeCount = nodes.length
  const angleStep = (2 * Math.PI) / nodeCount
  
  const nodePositions = {}
  
  nodes.forEach((node, index) => {
    const angle = angleStep * index - Math.PI / 2
    nodePositions[node.id] = {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle)
    }
  })
  
  links.forEach(link => {
    const sourcePos = nodePositions[link.source]
    const targetPos = nodePositions[link.target]
    
    if (!sourcePos || !targetPos) return
    
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
    line.setAttribute('x1', sourcePos.x)
    line.setAttribute('y1', sourcePos.y)
    line.setAttribute('x2', targetPos.x)
    line.setAttribute('y2', targetPos.y)
    line.setAttribute('stroke', link.statusColor || '#6b7280')
    line.setAttribute('stroke-width', '2')
    line.setAttribute('data-connection', JSON.stringify(link))
    line.style.cursor = 'pointer'
    line.addEventListener('click', () => {
      selectedConnection.value = link
    })
    svg.appendChild(line)
  })
  
  nodes.forEach(node => {
    const pos = nodePositions[node.id]
    if (!pos) return
    
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g')
    g.setAttribute('transform', `translate(${pos.x}, ${pos.y})`)
    g.style.cursor = 'pointer'
    
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
    circle.setAttribute('r', '25')
    circle.setAttribute('fill', node.statusColor || '#6b7280')
    circle.setAttribute('stroke', '#fff')
    circle.setAttribute('stroke-width', '2')
    g.appendChild(circle)
    
    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text')
    label.setAttribute('text-anchor', 'middle')
    label.setAttribute('dy', '40')
    label.setAttribute('fill', '#fff')
    label.setAttribute('font-size', '12')
    label.textContent = node.label
    g.appendChild(label)
    
    const countLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text')
    countLabel.setAttribute('text-anchor', 'middle')
    countLabel.setAttribute('dy', '5')
    countLabel.setAttribute('fill', '#fff')
    countLabel.setAttribute('font-size', '10')
    countLabel.setAttribute('font-weight', 'bold')
    countLabel.textContent = node.requests || '0'
    g.appendChild(countLabel)
    
    g.addEventListener('click', () => {
      selectedNode.value = node
    })
    
    svg.appendChild(g)
  })
}

watch(topology, renderGraph, { deep: true })

onMounted(() => {
  connectWebSocket()
  renderGraph()
})

onUnmounted(() => {
  if (ws) ws.close()
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.topology-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1a1a2e;
  color: #e0e0e0;
  padding: 1rem;
}

.topology-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.topology-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.controls {
  display: flex;
  gap: 0.5rem;
}

.controls button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-refresh {
  background: #3b82f6;
  color: white;
}

.btn-reset {
  background: #6b7280;
  color: white;
}

.btn-auto {
  background: #374151;
  color: white;
}

.btn-auto.active {
  background: #22c55e;
}

.health-summary {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 1rem;
  background: #16213e;
  border-radius: 8px;
}

.health-card {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  text-align: center;
}

.health-card.healthy {
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid #22c55e;
}

.health-card.degraded {
  background: rgba(234, 179, 8, 0.2);
  border: 1px solid #eab308;
}

.health-card.critical {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid #ef4444;
}

.health-label {
  display: block;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.health-value {
  display: block;
  font-size: 1.25rem;
  font-weight: bold;
  text-transform: capitalize;
}

.health-stat {
  padding: 0.75rem 1rem;
  background: #1f2937;
  border-radius: 6px;
  text-align: center;
}

.health-stat.healthy .stat-value {
  color: #22c55e;
}

.health-stat.error .stat-value {
  color: #ef4444;
}

.stat-label {
  display: block;
  font-size: 0.75rem;
  color: #9ca3af;
}

.stat-value {
  display: block;
  font-size: 1.25rem;
  font-weight: bold;
}

.graph-container {
  flex: 1;
  position: relative;
  background: #0f0f23;
  border-radius: 8px;
  overflow: hidden;
  min-height: 400px;
}

.topology-svg {
  width: 100%;
  height: 100%;
}

.legend {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  display: flex;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 4px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-dot.healthy {
  background: #22c55e;
}

.legend-dot.slow {
  background: #eab308;
}

.legend-dot.error {
  background: #ef4444;
}

.node-details,
.connection-details {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 280px;
  background: #16213e;
  border-radius: 8px;
  overflow: hidden;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #1f2937;
}

.details-header h3 {
  margin: 0;
  font-size: 1rem;
}

.btn-close {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 1.5rem;
  cursor: pointer;
}

.details-body {
  padding: 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.detail-row .label {
  color: #9ca3af;
}

.detail-row .value {
  font-weight: bold;
}

.detail-row .value.healthy {
  color: #22c55e;
}

.detail-row .value.slow {
  color: #eab308;
}

.detail-row .value.error {
  color: #ef4444;
}

.endpoints-list {
  margin: 0;
  padding-left: 1rem;
  font-size: 0.75rem;
  color: #9ca3af;
  max-height: 100px;
  overflow-y: auto;
}
</style>
