class WebSocketManager {
  constructor () {
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://'
    this.url = `${protocol}${window.location.host}/ws/sync/`
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 10
    this.reconnectInterval = 1000
    this.heartbeatInterval = 60000
    this.heartbeatTimer = null
    this.listeners = new Map()

    this.connect()
  }

  connect () {
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      console.log('WebSocket conectado')
      this.reconnectAttempts = 0
      this.startHeartbeat()
      this.emit('connected')
    }

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      // Responder pings automaticamente
      if (data.type === 'ping') {
        const now = Date.now() / 1000
        this.send({ type: 'pong', timestamp_client: now })
        return
      } else if (data.type === 'pong') {
        let pong_now = performance.now() // Date.now() / 1000 // em segundos
        const now = {
          type: 'pong',
          pong: pong_now,
          ping: data.message.ping_now,
          timestamp_client: data.message.timestamp_client,
          timestamp_server: data.message.timestamp_server,
          // latency: pong_now - data.ping_now,
          server_time_diff: data.message.timestamp_server - data.message.timestamp_client - (pong_now - data.message.ping_now) / 1000
        }
        // console.log('Pong recebido do servidor:', now)
        this.emit('message', now)
        return
      }
      this.emit('message', data)
    }

    this.ws.onclose = (e) => {
      console.log('WebSocket desconectado', e)
      this.stopHeartbeat()
      this.emit('disconnected')
      this.handleReconnect()
    }

    this.ws.onerror = (error) => {
      console.error('Erro WebSocket:', error)
      this.emit('error', error)
    }
  }

  handleReconnect () {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay =
        this.reconnectInterval * Math.pow(2, this.reconnectAttempts)

      setTimeout(() => {
        console.log(`Tentativa de reconexão ${this.reconnectAttempts}`)
        this.connect()
      }, delay)
    }
  }

  startHeartbeat () {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        const now = Date.now() / 1000
        this.send({ type: 'ping', timestamp_client: now, ping_now: performance.now() })
      }
    }, this.heartbeatInterval)
  }

  stopHeartbeat () {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  send (data) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  on (event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  emit (event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach((callback) => callback(data))
    }
  }
}

export default WebSocketManager
