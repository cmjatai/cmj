var intervalIds = {}

self.onmessage = function (e) {
  switch (e.data.command) {
    case 'interval:start':
      var intvalId = setInterval(function () {
        postMessage({
          message: 'interval:tick',
          id: e.data.id
        })
      }, e.data.interval)

      postMessage({
        message: 'interval:started',
        id: e.data.id
      })

      intervalIds[e.data.id] = intvalId
      break

    case 'interval:clear':
      clearInterval(intervalIds[e.data.id])

      postMessage({
        message: 'interval:cleared',
        id: e.data.id
      })

      delete intervalIds[e.data.id]
      break
  }
}
