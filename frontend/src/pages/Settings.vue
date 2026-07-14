<template>
  <div>
    <h2 class="text-xl font-bold mb-4">设置</h2>

    <!-- 汇率配置（只读） -->
    <t-card title="汇率配置" class="mb-4">
      <t-table :data="rates" :columns="rateColumns" row-key="currency" :loading="loadingRates" />
    </t-card>

    <!-- 平台可用性监测 -->
    <t-card title="平台可用性监测" class="mb-4">
      <!-- 数据源服务 -->
      <h3 class="text-base font-medium mb-3">数据源服务</h3>
      <div class="flex items-center gap-3 mb-3">
        <t-button :loading="testingDataSource" @click="runDiagnostics('datasource')">
          延迟测试
        </t-button>
        <span v-if="lastTestedDatasource" class="text-sm text-gray-500">
          上次测试：{{ lastTestedDatasource }}
        </span>
      </div>
      <t-table
        :data="datasourceServices"
        :columns="datasourceColumns"
        row-key="name"
        :loading="testingDataSource"
      >
        <template #status="{ row }">
          <span v-if="row" :style="{ color: statusColor(row.status), display: 'flex', alignItems: 'center', gap: '4px' }">
            <t-icon :name="statusIcon(row.status)" /> {{ statusLabel(row.status) }}
          </span>
        </template>
        <template #usage="{ row }">
          {{ row ? (row.usage || '-') : '' }}
        </template>
        <template #registration="{ row }">
          {{ row ? (row.registration_type || '-') : '' }}
        </template>
        <template #latency="{ row }">
          {{ row && row.latency_ms > 0 ? row.latency_ms : '-' }}
        </template>
        <template #checked_at="{ row }">
          {{ row ? formatTime(row.checked_at) : '' }}
        </template>
      </t-table>

      <!-- 大模型服务 -->
      <h3 class="text-base font-medium mb-3 mt-6">大模型服务</h3>
      <div class="flex items-center gap-3 mb-3">
        <t-button :loading="testingLLM" @click="runDiagnostics('llm')">
          延迟测试
        </t-button>
        <span v-if="lastTestedLLM" class="text-sm text-gray-500">
          上次测试：{{ lastTestedLLM }}
        </span>
      </div>
      <t-table
        :data="llmServices"
        :columns="llmColumns"
        row-key="name"
        :loading="testingLLM"
      >
        <template #status="{ row }">
          <span v-if="row" :style="{ color: statusColor(row.status), display: 'flex', alignItems: 'center', gap: '4px' }">
            <t-icon :name="statusIcon(row.status)" /> {{ statusLabel(row.status) }}
          </span>
        </template>
        <template #usage="{ row }">
          {{ row ? (row.usage || '-') : '' }}
        </template>
        <template #registration="{ row }">
          {{ row ? (row.registration_type || '-') : '' }}
        </template>
        <template #latency="{ row }">
          {{ row && row.latency_ms > 0 ? row.latency_ms : '-' }}
        </template>
        <template #checked_at="{ row }">
          {{ row ? formatTime(row.checked_at) : '' }}
        </template>
      </t-table>

      <!-- 版本信息 -->
      <div v-if="versions" class="mt-6 pt-4 border-t border-gray-200">
        <h3 class="text-base font-medium mb-2">版本信息</h3>
        <div class="text-sm text-gray-600 space-y-1">
          <div>项目版本：{{ versions.project_version }}</div>
          <div>数据库版本：{{ versions.db_version }}</div>
        </div>
      </div>
    </t-card>

    <!-- 数据备份 -->
    <t-card title="数据备份" class="mb-4">
      <div class="space-y-2">
        <t-checkbox-group v-model="backupTypes">
          <t-checkbox value="stocks">个股列表（含标签）</t-checkbox>
          <t-checkbox value="capital_flows">现金流记录</t-checkbox>
          <t-checkbox value="transactions">交易记录</t-checkbox>
          <t-checkbox value="memos">投资备忘</t-checkbox>
          <t-checkbox value="kline">K 线数据</t-checkbox>
        </t-checkbox-group>
      </div>
      <div class="flex items-center gap-3 mt-4">
        <t-button :loading="exporting" @click="handleExport" :disabled="backupTypes.length === 0">导出</t-button>
        <t-button :loading="importing" @click="triggerImport">导入</t-button>
        <input ref="fileInputRef" type="file" accept=".zip" class="hidden" @change="handleImport" />
      </div>

      <!-- 导入结果 -->
      <t-alert v-if="importResult" :theme="importResult.theme" :message="importResult.message" class="mt-4" closable @close="importResult = null" />
    </t-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listExchangeRates } from '@/api/exchangeRates'
import { listServicesApi, runDiagnosticsApi, type DiagnosticItem, type ServiceMeta, type VersionInfo } from '@/api/diagnostics'
import { exportBackupApi, importBackupApi } from '@/api/backup'
import { getCapitalSummary } from '@/api/capital'
import type { ExchangeRateItem } from '@/api/exchangeRates'
import { usePortfolioStore } from '@/stores/portfolio'
import { MessagePlugin } from 'tdesign-vue-next'

const LS_KEY = 'stockmemos_diagnostics'

const loadingRates = ref(false)
const rates = ref<ExchangeRateItem[]>([])

const rateColumns = [
  { colKey: 'currency', title: '币种', width: 100 },
  { colKey: 'rate_to_cny', title: '兑人民币汇率', width: 180 },
  { colKey: 'updated_at', title: '更新时间', width: 200 },
]

async function loadRates() {
  loadingRates.value = true
  const r = await listExchangeRates()
  loadingRates.value = false
  if (r.ok && r.data) {
    rates.value = r.data
  }
}

// ─── 诊断 ─────────────────────────────────────

const testingDataSource = ref(false)
const testingLLM = ref(false)
const lastTestedDatasource = ref('')
const lastTestedLLM = ref('')
const datasourceServices = ref<DiagnosticItem[]>([])
const llmServices = ref<DiagnosticItem[]>([])
const versions = ref<VersionInfo | null>(null)

const datasourceColumns = [
  { colKey: 'name', title: '名称', width: 180 },
  { colKey: 'usage', title: '被用于', width: 120, cell: 'usage' },
  { colKey: 'registration', title: '注册方式', width: 140, cell: 'registration' },
  { colKey: 'status', title: '状态', width: 100, cell: 'status' },
  { colKey: 'latency', title: '延迟 (ms)', width: 120, cell: 'latency' },
  { colKey: 'checked_at', title: '检测时间', width: 200, cell: 'checked_at' },
]

const llmColumns = [
  { colKey: 'name', title: '名称', width: 180 },
  { colKey: 'usage', title: '被用于', width: 120, cell: 'usage' },
  { colKey: 'registration', title: '注册方式', width: 140, cell: 'registration' },
  { colKey: 'status', title: '状态', width: 100, cell: 'status' },
  { colKey: 'latency', title: '延迟 (ms)', width: 120, cell: 'latency' },
  { colKey: 'checked_at', title: '检测时间', width: 200, cell: 'checked_at' },
]

function statusColor(status: string): string {
  return { ok: 'green', error: 'red', skipped: 'gray' }[status] || 'gray'
}

function statusIcon(status: string): string {
  return {
    ok: 'check-circle-filled',
    error: 'close-circle-filled',
    skipped: 'info-circle-filled',
  }[status] || 'info-circle-filled'
}

function statusLabel(status: string): string {
  return { ok: '正常', error: '异常', skipped: '跳过' }[status] || status
}

function formatTime(isoStr: string): string {
  if (!isoStr) return ''
  // Convert "2026-07-13T08:46:18Z" to "2026-07-13 08:46:18"
  return isoStr.replace('T', ' ').replace(/\.\d+Z$/, '').replace('Z', '')
}

function setServices(data: DiagnosticItem[]) {
  datasourceServices.value = data.filter(s => s.category === 'datasource')
  llmServices.value = data.filter(s => s.category === 'llm')
}

function saveToLS(data: DiagnosticItem[], ver: VersionInfo, ts: string) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify({
      services: data,
      versions: ver,
      checked_at: ts,
    }))
  } catch {
    // localStorage full or unavailable - ignore
  }
}

function loadFromLS() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return
    const saved = JSON.parse(raw)
    if (saved.services && Array.isArray(saved.services)) {
      setServices(saved.services)
    }
    if (saved.versions) {
      versions.value = saved.versions
    }
    if (saved.checked_at) {
      const formatted = formatTime(saved.checked_at)
      lastTestedDatasource.value = formatted
      lastTestedLLM.value = formatted
    }
  } catch {
    // ignore parse errors
  }
}

async function runDiagnostics(scope: 'datasource' | 'llm') {
  if (scope === 'datasource') {
    testingDataSource.value = true
  } else {
    testingLLM.value = true
  }

  const r = await runDiagnosticsApi(scope)
  if (scope === 'datasource') {
    testingDataSource.value = false
  } else {
    testingLLM.value = false
  }

  if (!r.ok || !r.data) return

  const data = r.data
  
  // Only update services for the requested scope; preserve other scope
  if (scope === 'datasource') {
    datasourceServices.value = data.services.filter(s => s.category === 'datasource')
  } else {
    llmServices.value = data.services.filter(s => s.category === 'llm')
  }
  versions.value = data.versions

  const formatted = formatTime(data.checked_at)
  if (scope === 'datasource') {
    lastTestedDatasource.value = formatted
  } else {
    lastTestedLLM.value = formatted
  }

  // Merge with existing LS data
  const existing = datasourceServices.value.concat(llmServices.value)
  saveToLS(existing, data.versions, data.checked_at)
}

// ─── 备份 ─────────────────────────────────────

const backupTypes = ref<string[]>(['stocks', 'transactions'])
const exporting = ref(false)
const importing = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const importResult = ref<{ theme: string; message: string } | null>(null)

function triggerImport() {
  fileInputRef.value?.click()
}

async function handleExport() {
  if (backupTypes.value.length === 0) {
    MessagePlugin.warning('请至少选择一项备份内容')
    return
  }
  exporting.value = true
  try {
    const r = await exportBackupApi(backupTypes.value)
    if (!r.ok) {
      MessagePlugin.error('导出失败')
      return
    }
    // Trigger download
    const blob = r.data as Blob
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `stockmemos_export_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    MessagePlugin.success('导出成功')
  } finally {
    exporting.value = false
  }
}

async function handleImport(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  const file = input.files[0]
  importing.value = true
  importResult.value = null
  try {
    const r = await importBackupApi(file)
    if (!r.ok || !r.data) {
      importResult.value = { theme: 'error', message: '导入失败，请检查文件格式' }
      return
    }
    const data = r.data
    const lines: string[] = []
    lines.push(`✅ 个股：${data.imported.stocks} 成功`)
    if (data.skipped.stocks.length > 0) {
      lines.push(`⏭ 跳过：${data.skipped.stocks.join(', ')}`)
    }
    lines.push(`✅ 交易：${data.imported.transactions} 成功`)
    lines.push(`✅ 现金流：${data.imported.capital_flows} 成功`)
    lines.push(`✅ 备忘：${data.imported.memos} 成功`)
    if (data.imported.kline_files > 0) {
      lines.push(`✅ K线文件：${data.imported.kline_files} 个`)
    }
    importResult.value = { theme: 'success', message: lines.join(' / ') }
    // 自动刷新后台数据
    usePortfolioStore().fetchAll()
    getCapitalSummary().then(r => {
      if (r.ok && r.data) {
        // capital summary 已通过 Pinia 缓存更新
      }
    })
    MessagePlugin.success('导入成功，数据已更新')
  } catch (e) {
    importResult.value = { theme: 'error', message: `导入出错: ${e}` }
  } finally {
    importing.value = false
    // Reset file input
    input.value = ''
  }
}

onMounted(async () => {
  loadRates()
  // 从 /diagnostics/services 获取静态元数据（名称/被用于/注册方式），即时展示
  const srv = await listServicesApi()
  if (srv.ok && srv.data) {
    const all = srv.data.services
    datasourceServices.value = all.filter(s => s.category === 'datasource') as DiagnosticItem[]
    llmServices.value = all.filter(s => s.category === 'llm') as DiagnosticItem[]
  }
  // 尝试从 localStorage 恢复上次检测结果
  loadFromLS()
})
</script>
