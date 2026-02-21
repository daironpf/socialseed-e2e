import { defineStore } from 'pinia'
import axios from 'axios'

const API = '/api'

export const useTestStore = defineStore('tests', {
  state: () => ({
    services: [],
    tests: [],
    selectedService: null,
    selectedTest: null,
    testResults: [],
    isLoading: false,
    isRunning: false,
    runProgress: 0
  }),

  getters: {
    testsByService: (state) => {
      const grouped = {}
      state.tests.forEach(test => {
        const service = test.service || 'unknown'
        if (!grouped[service]) grouped[service] = []
        grouped[service].push(test)
      })
      return grouped
    },
    
    passedCount: (state) => state.testResults.filter(r => r.status === 'passed').length,
    failedCount: (state) => state.testResults.filter(r => r.status === 'failed').length,
    totalDuration: (state) => state.testResults.reduce((sum, r) => sum + (r.duration || 0), 0)
  },

  actions: {
    async loadTests() {
      this.isLoading = true
      try {
        const { data } = await axios.get(`${API}/tests`)
        this.services = data.services || []
        this.tests = data.tests || []
      } catch (error) {
        console.error('Failed to load tests:', error)
      } finally {
        this.isLoading = false
      }
    },

    async runTest(testPath, params = {}) {
      this.isRunning = true
      try {
        const { data } = await axios.post(`${API}/tests/run`, {
          test_path: testPath,
          params
        })
        this.testResults.unshift(data.result)
        return data.result
      } catch (error) {
        console.error('Test run failed:', error)
        throw error
      } finally {
        this.isRunning = false
      }
    },

    async runAllTests(service = null) {
      this.isRunning = true
      this.runProgress = 0
      const testsToRun = service 
        ? this.tests.filter(t => t.service === service)
        : this.tests
      
      const total = testsToRun.length
      let completed = 0
      
      for (const test of testsToRun) {
        try {
          const result = await this.runTest(test.path)
          this.testResults.unshift(result)
        } catch (error) {
          this.testResults.unshift({
            test: test.name,
            status: 'error',
            error: error.message
          })
        }
        completed++
        this.runProgress = Math.round((completed / total) * 100)
      }
      
      this.isRunning = false
    },

    selectService(service) {
      this.selectedService = service
    },

    selectTest(test) {
      this.selectedTest = test
    },

    addResult(result) {
      this.testResults.unshift(result)
    }
  }
})
