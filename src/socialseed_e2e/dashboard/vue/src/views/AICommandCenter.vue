<template>
  <div class="ai-command-center">
    <!-- EPIC-007: AI Prompt Command Center -->
    
    <div class="chat-container">
      <!-- Chat Messages -->
      <div class="messages" ref="messagesContainer">
        <div 
          v-for="(msg, index) in messages" 
          :key="index"
          :class="['message', msg.role]"
        >
          <div class="avatar">
            {{ msg.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="content">
            <div class="message-header">
              <span class="sender">{{ msg.role === 'user' ? 'You' : 'AI Agent' }}</span>
              <span class="time">{{ formatTime(msg.timestamp) }}</span>
            </div>
            <div class="message-body" v-html="renderMarkdown(msg.content)"></div>
            <div v-if="msg.commands" class="commands-executed">
              <span class="label">Commands executed:</span>
              <code v-for="cmd in msg.commands" :key="cmd">{{ cmd }}</code>
            </div>
          </div>
        </div>
        
        <!-- Typing Indicator -->
        <div v-if="isTyping" class="message ai typing">
          <div class="avatar">🤖</div>
          <div class="content">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Input Area -->
      <div class="input-area">
        <div class="quick-actions">
          <button 
            v-for="action in quickActions" 
            :key="action.label"
            @click="executeQuickAction(action)"
            :title="action.label"
          >
            {{ action.icon }}
          </button>
        </div>
        <div class="input-wrapper">
          <textarea 
            v-model="userInput" 
            @keydown.enter.exact="sendMessage"
            @keydown.shift.enter="newLine"
            placeholder="Ask the AI agent... (Enter to send, Shift+Enter for new line)"
            rows="1"
          ></textarea>
          <button @click="sendMessage" :disabled="!userInput.trim()" class="send-btn">
            ➤
          </button>
        </div>
        <div class="input-hint">
          Try: "Analyze error at 10am" or "Generate regression test for auth"
        </div>
      </div>
    </div>
    
    <!-- Context Panel -->
    <div class="context-panel" :class="{ expanded: contextExpanded }">
      <div class="panel-header" @click="contextExpanded = !contextExpanded">
        <span>Context</span>
        <span>{{ contextExpanded ? '▼' : '▶' }}</span>
      </div>
      <div v-if="contextExpanded" class="panel-content">
        <div class="context-section">
          <h4>Available Services</h4>
          <div class="tags">
            <span v-for="s in services" :key="s" class="tag">{{ s }}</span>
          </div>
        </div>
        <div class="context-section">
          <h4>Recent Incidents</h4>
          <div class="incident-list">
            <div 
              v-for="inc in incidents" 
              :key="inc.id"
              class="incident-item"
              @click="selectIncident(inc)"
            >
              <span class="incident-id">{{ inc.id }}</span>
              <span :class="['severity', inc.severity]">{{ inc.severity }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'

// State
const messages = ref([
  {
    role: 'ai',
    content: 'Hello! I am your AI Testing Assistant. I can help you:\n\n- **Analyze** traffic and errors\n- **Generate** E2E tests\n- **Debug** failed requests\n- **Run** test suites\n\nWhat would you like me to do?',
    timestamp: new Date(),
    commands: []
  }
])

const userInput = ref('')
const isTyping = ref(false)
const messagesContainer = ref(null)
const contextExpanded = ref(false)
const services = ref(['auth-service', 'socialuser-service', 'post-service'])
const incidents = ref([
  { id: 'INC-abc123', severity: 'critical' },
  { id: 'INC-def456', severity: 'warning' },
  { id: 'INC-ghi789', severity: 'info' }
])

const quickActions = [
  { icon: '🔍', label: 'Analyze errors', prompt: 'Analyze recent errors' },
  { icon: '🧪', label: 'Generate test', prompt: 'Generate a regression test' },
  { icon: '📊', label: 'Show stats', prompt: 'Show test statistics' },
  { icon: '▶️', label: 'Run tests', prompt: 'Run all test suites' }
]

// Methods
function formatTime(date) {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function renderMarkdown(text) {
  // Simple markdown rendering
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

async function sendMessage() {
  if (!userInput.value.trim()) return
  
  const userMessage = userInput.value
  userInput.value = ''
  
  // Add user message
  messages.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date()
  })
  
  // Show typing indicator
  isTyping.value = true
  scrollToBottom()
  
  // Process with AI (simulated for now)
  const response = await processWithAI(userMessage)
  
  // Add AI response
  messages.value.push({
    role: 'ai',
    content: response.content,
    timestamp: new Date(),
    commands: response.commands || []
  })
  
  isTyping.value = false
  scrollToBottom()
}

async function processWithAI(prompt) {
  // Simulated AI processing
  // In production, this would connect to the AI modules
  
  await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000))
  
  const promptLower = prompt.toLowerCase()
  
  if (promptLower.includes('analyze') || promptLower.includes('error')) {
    return {
      content: `## Analysis Complete\n\nI found **3 error clusters** in the recent traffic:\n\n1. **INC-abc123** - 500 errors on /api/users at 10:15 AM\n2. **INC-def456** - 401 errors on /auth/login at 10:23 AM\n3. **INC-ghi789** - 404 errors on /api/posts at 10:45 AM\n\nWould you like me to generate tests to cover these scenarios?`,
      commands: ['e2e time-machine list --limit 10']
    }
  }
  
  if (promptLower.includes('generate') || promptLower.includes('test')) {
    return {
      content: `## Test Generation\n\nI've analyzed the traffic patterns and generated the following test modules:\n\n- `01_auth_flow.py` - Authentication flow\n- `02_user_crud.py` - User CRUD operations\n- `03_error_recovery.py` - Error handling tests\n\nTests saved to: \`services/auth-service/modules/\``,
      commands: ['e2e generate-tests --service auth-service']
    }
  }
  
  if (promptLower.includes('run')) {
    return {
      content: `## Running Tests\n\nExecuting test suite for auth-service...\n\n\`\`\`\n✓ 15 tests passed\n✓ 3 tests passed\n✓ 2 tests passed\n\`\`\`\n\n**Summary: 20/20 tests passed (100%)**`,
      commands: ['e2e run --service auth-service']
    }
  }
  
  return {
    content: `I understand you're asking about: "${prompt}"\n\nI can help you with:\n- Analyzing traffic and errors\n- Generating E2E tests\n- Debugging failed requests\n- Running test suites\n\nCould you be more specific about what you'd like me to do?`,
    commands: []
  }
}

function executeQuickAction(action) {
  userInput.value = action.prompt
  sendMessage()
}

function selectIncident(inc) {
  userInput.value = `Analyze incident ${inc.id} and generate a test`
  sendMessage()
}

function newLine(event) {
  // Allow new line with Shift+Enter
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.ai-command-center {
  height: 100%;
  display: flex;
  background: #1e1e1e;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  display: flex;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #333;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.content {
  max-width: 70%;
  margin: 0 12px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 12px;
}

.sender {
  font-weight: bold;
  color: #d4d4d4;
}

.time {
  color: #858585;
}

.message-body {
  background: #2d2d2d;
  padding: 12px 16px;
  border-radius: 12px;
  color: #d4d4d4;
  line-height: 1.5;
}

.message.user .message-body {
  background: #0e639c;
}

.message.ai .message-body {
  background: #252526;
}

.commands-executed {
  margin-top: 8px;
  padding: 8px;
  background: #1e1e1e;
  border-radius: 4px;
  font-size: 11px;
}

.commands-executed .label {
  color: #858585;
  margin-right: 8px;
}

.commands-executed code {
  background: #333;
  padding: 2px 6px;
  border-radius: 3px;
  margin-right: 5px;
  color: #4ec9b0;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 10px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #858585;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-5px); }
}

.input-area {
  padding: 15px;
  background: #252526;
  border-top: 1px solid #3e3e42;
}

.quick-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.quick-actions button {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  background: #333;
  cursor: pointer;
  font-size: 18px;
}

.quick-actions button:hover {
  background: #444;
}

.input-wrapper {
  display: flex;
  gap: 10px;
}

.input-wrapper textarea {
  flex: 1;
  background: #3c3c3c;
  border: 1px solid #3e3e42;
  border-radius: 8px;
  padding: 10px 15px;
  color: #d4d4d4;
  font-family: inherit;
  resize: none;
}

.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  border: none;
  background: #0e639c;
  color: white;
  font-size: 18px;
  cursor: pointer;
}

.send-btn:disabled {
  background: #333;
  color: #666;
}

.input-hint {
  margin-top: 8px;
  font-size: 11px;
  color: #666;
}

.context-panel {
  width: 280px;
  background: #252526;
  border-left: 1px solid #3e3e42;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 15px;
  cursor: pointer;
  font-weight: bold;
  border-bottom: 1px solid #3e3e42;
}

.panel-content {
  padding: 15px;
  overflow-y: auto;
}

.context-section {
  margin-bottom: 20px;
}

.context-section h4 {
  margin: 0 0 10px;
  color: #858585;
  font-size: 12px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.tag {
  background: #333;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #4ec9b0;
}

.incident-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.incident-item {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: #333;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.incident-item:hover {
  background: #444;
}

.severity.critical { color: #f14c4c; }
.severity.warning { color: #cca700; }
.severity.info { color: #569cd6; }
</style>