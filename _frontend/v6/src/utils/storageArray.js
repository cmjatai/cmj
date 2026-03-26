export function addArrayOfIds (key, id) {
  const arr = getArrayOfIds(key)
  if (arr.indexOf(id) === -1) {
    arr.push(id)
    localStorage.setItem(key, JSON.stringify(arr))
  }
}

export function getArrayOfIds (key) {
  const value = localStorage.getItem(key)
  if (value) {
    try {
      return JSON.parse(value)
    } catch (e) {
      return []
    }
  }
  return []
}

export function inArrayOfIds (key, id) {
  const arr = getArrayOfIds(key)
  return arr.indexOf(id) !== -1
}

export function delItemArrayOfIds (key, id) {
  const arr = getArrayOfIds(key)
  const idx = arr.indexOf(id)
  if (idx !== -1) {
    arr.splice(idx, 1)
    localStorage.setItem(key, JSON.stringify(arr))
  }
}

export function clearArrayOfIds (key) {
  localStorage.removeItem(key)
}
