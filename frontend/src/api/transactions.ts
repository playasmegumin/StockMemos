import { wrapResult } from './client'
import type { Result } from '@/types/api'
import type { Transaction, TransactionCreate, TransactionUpdate } from '@/types/transaction'

export function listTransactions(): Promise<Result<Transaction[]>> {
  return wrapResult<Transaction[]>({ method: 'GET', url: '/transactions' })
}

export function getTransactionsByStock(stockId: string): Promise<Result<Transaction[]>> {
  return wrapResult<Transaction[]>({ method: 'GET', url: `/transactions/stock/${stockId}`, dedup: true })
}

export function createTransaction(data: TransactionCreate): Promise<Result<Transaction>> {
  return wrapResult<Transaction>({ method: 'POST', url: '/transactions', data })
}

export function updateTransaction(id: string, data: TransactionUpdate): Promise<Result<Transaction>> {
  return wrapResult<Transaction>({ method: 'PUT', url: `/transactions/${id}`, data })
}

export function deleteTransaction(id: string): Promise<Result<true>> {
  return wrapResult<true>({ method: 'DELETE', url: `/transactions/${id}` })
}
