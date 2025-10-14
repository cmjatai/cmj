
import { ref, onMounted, onUnmounted, watch, inject } from 'vue'

/**
 * Vue 3 composable for managing WebSocket connections
 * @param {string} url - WebSocket server URL
 * @param {Object} options - Configuration options
 * @returns {Object} WebSocket connection utilities
 */

export function useWsTimeRefresh(url, options = {}) {
  const socket = ref(null)
  const isConnected = ref(false)
  const message = ref(null)
  const error = ref(null)

  const EventBus = inject('EventBus')

  // Configuration with defaults
  const config = {
    autoReconnect: true,
    reconnectInterval: 1000,
    maxReconnectAttempts: 5,
    ...options
  }

  let reconnectAttempts = 0
  let reconnectTimer = null

  // Connect to WebSocket server
  const connect = () => {
    if (socket.value && (socket.value.readyState === WebSocket.OPEN || socket.value.readyState === WebSocket.CONNECTING)) {
      return
    }

    try {
      socket.value = new WebSocket(url)

      socket.value.onopen = () => {
        isConnected.value = true
        error.value = null
        reconnectAttempts = 0
        console.log('WebSocket connected to', url)
      }

      socket.value.onmessage = (event) => {
        message.value = event.data
        try {
          const msgjson =JSON.parse(event.data)
          message.value = msgjson.message
          EventBus.emit('time-refresh', msgjson.message)
        } catch (err) {
          console.debug('Erro na conversão de JSON inválido.:', err)
        }
      }

      socket.value.onerror = (event) => {
        error.value = new Error('WebSocket error')
        console.error('WebSocket error:', event)
      }

      socket.value.onclose = () => {
        isConnected.value = false
        handleReconnect()
      }
    } catch (err) {
      error.value = err
      handleReconnect()
    }
  }

  // Handle reconnection logic
  const handleReconnect = () => {
    if (!config.autoReconnect || reconnectAttempts >= config.maxReconnectAttempts) {
      return
    }

    clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(() => {
      reconnectAttempts++
      connect()
    }, config.reconnectInterval * Math.pow(1.5, reconnectAttempts))
  }

  // Disconnect from WebSocket server
  const disconnect = () => {
    if (socket.value) {
      socket.value.close()
      isConnected.value = false
    }
    clearTimeout(reconnectTimer)
  }

  // Send data through the WebSocket
  const send = (data) => {
    if (!socket.value || socket.value.readyState !== WebSocket.OPEN) {
      error.value = new Error('WebSocket não conectado')
      return false
    }

    try {
      const payload = typeof data === 'string' ? data : JSON.stringify(data)
      socket.value.send(payload)
      return true
    } catch (err) {
      error.value = err
      return false
    }
  }

  // Setup the WebSocket connection
  onMounted(() => {
    connect()
  })

  // Clean up when component unmounts
  onUnmounted(() => {
    disconnect()
  })

  // Allow watching the URL for changes
  watch(() => url, (newUrl, oldUrl) => {
    if (newUrl !== oldUrl) {
      disconnect()
      connect()
    }
  })

  return {
    socket,
    isConnected,
    message,
    error,
    connect,
    disconnect,
    send,
  }
}
