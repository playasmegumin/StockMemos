import { describe, it, expect, vi, beforeEach } from 'vitest'
import { wrapResult } from '@/api/client'
import MockAdapter from 'axios-mock-adapter'
import client from '@/api/client'

let mock: MockAdapter

beforeEach(() => {
  mock = new MockAdapter(client)
})

describe('wrapResult', () => {
  it('returns ok: true on success', async () => {
    mock.onGet('/stocks').reply(200, [{ id: '1' }])
    const result = await wrapResult<any[]>({ method: 'GET', url: '/stocks' })
    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.data).toHaveLength(1)
    }
  })

  it('returns ok: false on network error', async () => {
    mock.onGet('/fail').networkError()
    const result = await wrapResult({ method: 'GET', url: '/fail' })
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error).toBeTruthy()
    }
  })

  it('returns ok: false on 4xx', async () => {
    mock.onGet('/stocks/x').reply(404, { detail: 'Not found' })
    const result = await wrapResult({ method: 'GET', url: '/stocks/x' })
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error).toContain('Not found')
    }
  })
})
