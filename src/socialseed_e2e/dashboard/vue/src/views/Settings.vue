<template>
  <div class="settings">
    <h2>Settings</h2>

    <div class="settings-grid">
      <div class="settings-section">
        <h3>General</h3>
        <div class="setting-item">
          <label class="setting-label">
            <span>Auto-refresh interval</span>
            <input 
              type="number" 
              v-model.number="settings.autoRefreshInterval" 
              class="setting-input"
              min="1"
              max="60"
            />
          </label>
          <span class="setting-hint">Seconds between auto-refresh (1-60)</span>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">
            <span>Max history entries</span>
            <input 
              type="number" 
              v-model.number="settings.maxHistoryEntries" 
              class="setting-input"
              min="10"
              max="1000"
            />
          </label>
          <span class="setting-hint">Maximum number of test results to keep (10-1000)</span>
        </div>
      </div>

      <div class="settings-section">
        <h3>Test Execution</h3>
        <div class="setting-item">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="settings.parallelExecution" 
              class="setting-checkbox"
            />
            <span>Enable parallel execution</span>
          </label>
          <span class="setting-hint">Run tests concurrently when possible</span>
        </div>
        
        <div class="setting-item">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="settings.retryFailedTests" 
              class="setting-checkbox"
            />
            <span>Auto-retry failed tests</span>
          </label>
          <span class="setting-hint">Automatically retry failed tests once</span>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">
            <span>Default timeout</span>
            <input 
              type="number" 
              v-model.number="settings.defaultTimeout" 
              class="setting-input"
              min="1000"
              max="120000"
              step="1000"
            />
          </label>
          <span class="setting-hint">Request timeout in milliseconds (1000-120000)</span>
        </div>
      </div>

      <div class="settings-section">
        <h3>Notifications</h3>
        <div class="setting-item">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="settings.notifyOnFailure" 
              class="setting-checkbox"
            />
            <span>Notify on test failure</span>
          </label>
          <span class="setting-hint">Show desktop notification when tests fail</span>
        </div>
        
        <div class="setting-item">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="settings.playSound" 
              class="setting-checkbox"
            />
            <span>Play sound on completion</span>
          </label>
          <span class="setting-hint">Play sound when test run completes</span>
        </div>
      </div>

      <div class="settings-section">
        <h3>API Configuration</h3>
        <div class="setting-item">
          <label class="setting-label">
            <span>Base URL</span>
            <input 
              type="text" 
              v-model="settings.baseUrl" 
              class="setting-input"
              placeholder="http://localhost:8080"
            />
          </label>
          <span class="setting-hint">Default API base URL</span>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">
            <span>API Key</span>
            <input 
              type="password" 
              v-model="settings.apiKey" 
              class="setting-input"
              placeholder="Enter API key"
            />
          </label>
          <span class="setting-hint">Optional API key for authenticated requests</span>
        </div>
      </div>

      <div class="settings-section">
        <h3>Dashboard</h3>
        <div class="setting-item">
          <label class="checkbox-label">
            <input 
              type="checkbox" 
              v-model="settings.darkMode" 
              class="setting-checkbox"
            />
            <span>Dark mode</span>
          </label>
          <span class="setting-hint">Use dark color scheme</span>
        </div>
        
        <div class="setting-item">
          <label class="setting-label">
            <span>Theme color</span>
            <input 
              type="color" 
              v-model="settings.themeColor" 
              class="setting-color"
            />
          </label>
          <span class="setting-hint">Primary color for the dashboard</span>
        </div>
      </div>

      <div class="settings-section">
        <h3>Data Management</h3>
        <div class="button-group">
          <button class="action-btn export" @click="exportData">
            📤 Export Data
          </button>
          <button class="action-btn import" @click="triggerImport">
            📥 Import Data
          </button>
          <input 
            type="file" 
            ref="fileInput" 
            @change="importData" 
            accept=".json"
            style="display: none"
          />
        </div>
        <div class="button-group">
          <button class="action-btn danger" @click="clearHistory">
            🗑️ Clear History
          </button>
          <button class="action-btn danger" @click="resetSettings">
            🔄 Reset to Defaults
          </button>
        </div>
      </div>
    </div>

    <div class="settings-actions">
      <button class="save-btn" @click="saveSettings">
        💾 Save Settings
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useTestStore } from '../stores/testStore'

const testStore = useTestStore()
const fileInput = ref(null)

const defaultSettings = {
  autoRefreshInterval: 5,
  maxHistoryEntries: 100,
  parallelExecution: true,
  retryFailedTests: false,
  defaultTimeout: 30000,
  notifyOnFailure: true,
  playSound: false,
  baseUrl: 'http://localhost:8080',
  apiKey: '',
  darkMode: false,
  themeColor: '#3b82f6'
}

const settings = reactive({ ...defaultSettings })

onMounted(() => {
  const saved = localStorage.getItem('e2e-dashboard-settings')
  if (saved) {
    try {
      Object.assign(settings, JSON.parse(saved))
    } catch {
      console.error('Failed to load settings')
    }
  }
})

const saveSettings = () => {
  localStorage.setItem('e2e-dashboard-settings', JSON.stringify(settings))
  testStore.showNotification('Settings saved successfully', 'success')
}

const exportData = () => {
  const data = {
    settings,
    testResults: testStore.testResults,
    exportedAt: new Date().toISOString()
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `e2e-dashboard-export-${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const triggerImport = () => {
  fileInput.value.click()
}

const importData = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result)
      if (data.settings) {
        Object.assign(settings, data.settings)
        localStorage.setItem('e2e-dashboard-settings', JSON.stringify(settings))
      }
      if (data.testResults) {
        testStore.testResults = data.testResults
      }
      testStore.showNotification('Data imported successfully', 'success')
    } catch {
      testStore.showNotification('Failed to import data', 'error')
    }
  }
  reader.readAsText(file)
}

const clearHistory = () => {
  if (confirm('Are you sure you want to clear all test history?')) {
    testStore.testResults = []
    testStore.showNotification('History cleared', 'success')
  }
}

const resetSettings = () => {
  if (confirm('Are you sure you want to reset all settings to defaults?')) {
    Object.assign(settings, defaultSettings)
    saveSettings()
  }
}
</script>

<style scoped>
.settings {
  max-width: 1000px;
  margin: 0 auto;
}

.settings h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
  color: #1f2937;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.settings-section {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.settings-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #1f2937;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.setting-item {
  margin-bottom: 1rem;
}

.setting-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.25rem;
}

.setting-input {
  padding: 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  width: 150px;
  font-size: 0.875rem;
}

.setting-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.setting-color {
  width: 50px;
  height: 35px;
  padding: 0;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  cursor: pointer;
}

.setting-checkbox {
  width: 1.25rem;
  height: 1.25rem;
  margin-right: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
}

.setting-hint {
  display: block;
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 0.25rem;
}

.button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.action-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.export,
.action-btn.import {
  background: #e0e7ff;
  color: #4338ca;
}

.action-btn.export:hover,
.action-btn.import:hover {
  background: #c7d2fe;
}

.action-btn.danger {
  background: #fee2e2;
  color: #991b1b;
}

.action-btn.danger:hover {
  background: #fecaca;
}

.settings-actions {
  margin-top: 2rem;
  display: flex;
  justify-content: flex-end;
}

.save-btn {
  padding: 0.75rem 2rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.save-btn:hover {
  background: #2563eb;
}
</style>
