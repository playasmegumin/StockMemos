import { describe, it, expect, vi, beforeEach } from 'vitest'
import { wrapResult } from '@/api/client'
import MockAdapter from 'axios-mock-adapter'
import client from '@/api/client'
import {
  listAdjustments,
  createAdjustment,
  updateAdjustment,
  deleteAdjustment,
} from '@/api/capital'
import type { HistoricalAdjustment, AdjustmentPayload } from '@/api/capital'

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

describe('HistoricalAdjustment API', () => {
  const adjustmentId = 'adj-001'

  const sampleAdjustment: HistoricalAdjustment = {
    id: adjustmentId,
    amount: 5000,
    note: '修正测试',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  }

  const samplePayload: AdjustmentPayload = {
    amount: 5000,
    note: '修正测试',
  }

  describe('listAdjustments', () => {
    it('GET /historical-adjustments returns list of adjustments', async () => {
      mock.onGet('/historical-adjustments').reply(200, [sampleAdjustment])

      const result = await listAdjustments()

      expect(result.ok).toBe(true)
      if (result.ok) {
        expect(result.data).toHaveLength(1)
        expect(result.data[0].id).toBe(adjustmentId)
        expect(result.data[0].amount).toBe(5000)
        expect(result.data[0].note).toBe('修正测试')
      }
    })

    it('GET /historical-adjustments propagates error', async () => {
      mock.onGet('/historical-adjustments').reply(500, { detail: 'Server error' })

      const result = await listAdjustments()

      expect(result.ok).toBe(false)
      if (!result.ok) {
        expect(result.error).toContain('Server error')
      }
    })
  })

  describe('createAdjustment', () => {
    it('POST /historical-adjustments sends payload and returns created adjustment', async () => {
      mock.onPost('/historical-adjustments', samplePayload).reply(201, sampleAdjustment)

      const result = await createAdjustment(samplePayload)

      expect(result.ok).toBe(true)
      if (result.ok) {
        expect(result.data.id).toBe(adjustmentId)
        expect(result.data.amount).toBe(5000)
        expect(result.data.note).toBe('修正测试')
      }
    })

    it('POST /historical-adjustments returns error on validation failure', async () => {
      mock.onPost('/historical-adjustments').reply(422, { detail: 'Validation failed' })

      const result = await createAdjustment({ amount: -1 })

      expect(result.ok).toBe(false)
      if (!result.ok) {
        expect(result.error).toContain('Validation failed')
      }
    })
  })

  describe('updateAdjustment', () => {
    const updatePayload: AdjustmentPayload = { amount: 6000, note: '更新修正' }
    const updatedAdjustment: HistoricalAdjustment = {
      ...sampleAdjustment,
      amount: 6000,
      note: '更新修正',
    }

    it('PUT /historical-adjustments/{id} sends payload and returns updated adjustment', async () => {
      mock.onPut(`/historical-adjustments/${adjustmentId}`, updatePayload).reply(200, updatedAdjustment)

      const result = await updateAdjustment(adjustmentId, updatePayload)

      expect(result.ok).toBe(true)
      if (result.ok) {
        expect(result.data.amount).toBe(6000)
        expect(result.data.note).toBe('更新修正')
      }
    })

    it('PUT /historical-adjustments/{id} returns error for unknown id', async () => {
      mock.onPut(`/historical-adjustments/${adjustmentId}`).reply(404, { detail: 'Not found' })

      const result = await updateAdjustment(adjustmentId, updatePayload)

      expect(result.ok).toBe(false)
      if (!result.ok) {
        expect(result.error).toContain('Not found')
      }
    })
  })

  describe('deleteAdjustment', () => {
    it('DELETE /historical-adjustments/{id} returns ok: true on success', async () => {
      mock.onDelete(`/historical-adjustments/${adjustmentId}`).reply(204)

      const result = await deleteAdjustment(adjustmentId)

      expect(result.ok).toBe(true)
      if (result.ok) {
        // Type-level check: data is `true`
        expect(result.data).toBe(true)
      }
    })

    it('DELETE /historical-adjustments/{id} returns error for unknown id', async () => {
      mock.onDelete(`/historical-adjustments/${adjustmentId}`).reply(404, { detail: 'Not found' })

      const result = await deleteAdjustment(adjustmentId)

      expect(result.ok).toBe(false)
      if (!result.ok) {
        expect(result.error).toContain('Not found')
      }
    })
  })
})
