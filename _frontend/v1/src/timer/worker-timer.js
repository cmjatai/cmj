import TimerWorker from './timer.worker.js'

const worker = new TimerWorker()

const workerTimer = {
  id: 0,
  callbacks: {},

  setInterval: function (cb, interval, context) {
    this.id++
    var id = this.id
    this.callbacks[id] = { fn: cb, context: context }
    worker.postMessage({
      command: 'interval:start',
      interval: interval,
      id: id
    })
    return id
  },

  onMessage: function (e) {
    switch (e.data.message) {
      case 'interval:tick':
        var callback = this.callbacks[e.data.id]
        if (callback && callback.fn) callback.fn.apply(callback.context)
        break
      case 'interval:cleared':
        delete this.callbacks[e.data.id]
        break
    }
  },

  clearInterval: function (id) {
    worker.postMessage({ command: 'interval:clear', id: id })
  }
}

worker.onmessage = workerTimer.onMessage.bind(workerTimer)

export default workerTimer
