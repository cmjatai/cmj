
class TimerWorkerService {
  constructor () {
    const url = window.location.host.includes('www')
      ? new URL('/static/v2025/js/workers/timer/timer.worker.js?t=' + Date.now(), import.meta.url).href
      : `${window.location.origin}/static/js/workers/timer/timer.worker.js?t=` + Date.now()
    this.worker = new Worker(url, { type: 'module' })
    this.callbacks = new Map()

    this.worker.onmessage = (e) => {
      const { type, timerId, timestamp } = e.data
      if (type === 'TIMER_TICK' && this.callbacks.has(timerId)) {
        this.callbacks.get(timerId)(timestamp)
      }
    }
  }

  startTimer (timerId, callback, interval = 1000) {
    this.callbacks.set(timerId, callback)
    this.worker.postMessage({
      type: 'START_TIMER',
      timerId,
      interval
    })
  }

  stopTimer (timerId) {
    this.callbacks.delete(timerId)
    this.worker.postMessage({
      type: 'STOP_TIMER',
      timerId
    })
  }
}

export default new TimerWorkerService()
