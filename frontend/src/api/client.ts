import axios from 'axios'
import type { AxiosRequestConfig } from 'axios'
import type { Result } from '@/types/api'

const client = axios.create({
  baseURL: '/api',
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request dedup ──
const inflight = new Map<string, Promise<Result<any>>>()

function dedupKey(config: AxiosRequestConfig): string {
  return `${config.method}:${config.url}:${JSON.stringify(config.params)}:${JSON.stringify(config.data)}`
}

/**
 * Wraps an axios call into a Result<T>.
 * If config.dedup is true, concurrent calls with the same key share one request.
 */
export async function wrapResult<T>(
  config: AxiosRequestConfig & { dedup?: boolean },
): Promise<Result<T>> {
  const key = dedupKey(config)

  // Dedup check
  if (config.dedup && inflight.has(key)) {
    return inflight.get(key)!
  }

  // Execute request, catch all errors into Result<T>
  const resultPromise = (async (): Promise<Result<T>> => {
    try {
      const resp = await client.request<T>(config)
      return { ok: true, data: resp.data }
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ??
        err?.message ??
        '网络连接失败'
      return { ok: false, error: msg }
    }
  })()

  if (config.dedup) {
    inflight.set(key, resultPromise)
    resultPromise.finally(() => inflight.delete(key))
  }

  return resultPromise
}

export default client
