function isApiReady() {
  const api = window.pywebview?.api
  return api && typeof api.get_app_info === 'function'
}

export function waitForPyWebView(timeout = 8000) {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    let settled = false

    const finish = (fn) => {
      if (settled) return
      settled = true
      clearInterval(poll)
      window.removeEventListener('pywebviewready', onReady)
      fn()
    }

    const tryResolve = () => {
      if (isApiReady()) {
        finish(() => resolve(window.pywebview.api))
        return true
      }
      return false
    }

    const onReady = () => tryResolve()
    window.addEventListener('pywebviewready', onReady)

    const poll = setInterval(() => {
      if (tryResolve()) return
      if (Date.now() - start > timeout) {
        finish(() => reject(new Error('PyWebView API 未就绪')))
      }
    }, 50)

    tryResolve()
  })
}

export async function callApi(method, ...args) {
  const api = await waitForPyWebView()
  if (typeof api[method] !== 'function') {
    throw new Error(`API 方法不存在: ${method}`)
  }
  return api[method](...args)
}
