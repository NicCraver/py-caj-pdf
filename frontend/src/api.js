export function waitForPyWebView(timeout = 8000) {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    const tick = () => {
      if (window.pywebview?.api) {
        resolve(window.pywebview.api)
        return
      }
      if (Date.now() - start > timeout) {
        reject(new Error('PyWebView API 未就绪'))
        return
      }
      setTimeout(tick, 50)
    }
    tick()
  })
}

export async function callApi(method, ...args) {
  const api = await waitForPyWebView()
  if (typeof api[method] !== 'function') {
    throw new Error(`API 方法不存在: ${method}`)
  }
  return api[method](...args)
}
