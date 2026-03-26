class TimerWorkerService {
  constructor () {
    this.worker = null
    this.callbacks = new Map()
    this.queue = []
    this.init()
  }

  init () {
    const workerCode = `
      let timers = new Map()

      self.onmessage = function (e) {
        const { type, timerId, interval } = e.data

        if (type === 'START_TIMER') {
          if (timers.has(timerId)) {
            clearInterval(timers.get(timerId))
          }

          const intervalId = setInterval(() => {
            self.postMessage({
              type: 'TIMER_TICK',
              timerId: timerId,
              timestamp: Date.now()
            })
          }, interval || 1000)

          timers.set(timerId, intervalId)
        }

        if (type === 'STOP_TIMER') {
          if (timers.has(timerId)) {
            clearInterval(timers.get(timerId))
            timers.delete(timerId)
          }
        }
      }
    `

    const blob = new Blob([workerCode], { type: 'application/javascript' })
    const workerUrl = URL.createObjectURL(blob)

    this.worker = new Worker(workerUrl)

    this.worker.onmessage = (e) => {
      const { type, timerId, timestamp } = e.data
      if (type === 'TIMER_TICK' && this.callbacks.has(timerId)) {
        this.callbacks.get(timerId)(timestamp)
      }
    }

    while (this.queue.length > 0) {
      const msg = this.queue.shift()
      this.worker.postMessage(msg)
    }
  }

  postMessage (msg) {
    if (this.worker) {
      this.worker.postMessage(msg)
    } else {
      this.queue.push(msg)
    }
  }

  startTimer (timerId, callback, interval = 1000) {
    this.callbacks.set(timerId, callback)
    this.postMessage({
      type: 'START_TIMER',
      timerId,
      interval
    })
  }

  stopTimer (timerId) {
    this.callbacks.delete(timerId)
    this.postMessage({
      type: 'STOP_TIMER',
      timerId
    })
  }
}

export default new TimerWorkerService()
