import { wrapResult } from './client'
import type { Result } from '@/types/api'

export interface DiagnosticItem {
  name: string
  status: 'ok' | 'error' | 'skipped'
  latency_ms: number
  error: string | null
  checked_at: string
  category: string
  usage: string
  registration_type: string
}

export interface ServiceMeta {
  name: string
  category: string
  usage: string
  registration_type: string
}

export interface ServicesResponse {
  services: ServiceMeta[]
}

export interface VersionInfo {
  project_version: string
  db_version: string
}

export interface DiagnosticsResponse {
  services: DiagnosticItem[]
  versions: VersionInfo
  total_latency_ms: number
  checked_at: string
}

export function listServicesApi(): Promise<Result<ServicesResponse>> {
  return wrapResult<ServicesResponse>({ method: 'GET', url: '/diagnostics/services' })
}

export function runDiagnosticsApi(scope?: 'datasource' | 'llm'): Promise<Result<DiagnosticsResponse>> {
  const params = scope ? `?scope=${scope}` : ''
  return wrapResult<DiagnosticsResponse>({ method: 'GET', url: `/diagnostics${params}` })
}
