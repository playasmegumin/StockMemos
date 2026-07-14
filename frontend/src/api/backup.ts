import { wrapResult } from './client'
import type { Result } from '@/types/api'

export interface BackupExportRequest {
  types: string[]
}

export interface BackupImportResult {
  imported: {
    stocks: number
    transactions: number
    memos: number
    capital_flows: number
    kline_files: number
  }
  skipped: {
    stocks: string[]
    transactions: number
    memos: number
    capital_flows: number
  }
}

export function exportBackupApi(types: string[]): Promise<Result<Blob>> {
  return wrapResult<Blob>({
    method: 'POST',
    url: '/backup/export',
    data: { types },
    responseType: 'blob',
  })
}

export function importBackupApi(file: File): Promise<Result<BackupImportResult>> {
  const formData = new FormData()
  formData.append('file', file)
  return wrapResult<BackupImportResult>({
    method: 'POST',
    url: '/backup/import',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
