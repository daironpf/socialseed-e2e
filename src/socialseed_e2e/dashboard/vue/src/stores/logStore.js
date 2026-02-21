import { defineStore } from 'pinia'

export const useLogStore = defineStore('logs', {
  state: () => ({
    logs: [],
    maxLogs: 500
  }),

  actions: {
    addLog(level, message) {
      this.logs.unshift({
        id: Date.now() + Math.random(),
        level,
        message,
        timestamp: new Date().toISOString()
      })
      
      if (this.logs.length > this.maxLogs) {
        this.logs.pop()
      }
    },

    clearLogs() {
      this.logs = []
    },

    addInfo(message) {
      this.addLog('info', message)
    },

    addSuccess(message) {
      this.addLog('success', message)
    },

    addError(message) {
      this.addLog('error', message)
    }
  }
})
