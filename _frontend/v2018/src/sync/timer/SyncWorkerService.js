// import Worker from './sync.worker.js'
class TimerWorkerService {
  constructor () {
    this.worker = new Worker(new URL('./sync.worker.js', import.meta.url))
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
