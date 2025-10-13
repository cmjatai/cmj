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
