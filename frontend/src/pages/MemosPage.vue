<template>
  <div class="memos-page p-6 max-w-3xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">投资备忘</h1>

    <!-- ═══ Editor Area (New / Edit) ═══ -->
    <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
      <div class="text-lg font-medium mb-4">
        {{ editingId ? '编辑备忘' : '新建备忘' }}
      </div>

      <!-- Title -->
      <div class="mb-4">
        <t-input
          v-model="form.title"
          placeholder="标题"
          size="large"
          maxlength="200"
          clearable
        />
      </div>

      <!-- Stock selector -->
      <div class="mb-4">
        <t-select
          v-model="form.stock_id"
          placeholder="关联个股（可选）"
          clearable
          filterable
          :options="stockOptions"
        />
      </div>

      <!-- Content -->
      <div class="mb-4">
        <t-textarea
          v-model="form.content"
          placeholder="写下你的投资思考…"
          :autosize="{ minRows: 5, maxRows: 15 }"
          style="font-size: 16px; line-height: 1.6"
        />
      </div>

      <!-- Actions -->
      <div class="flex gap-3">
        <t-button theme="primary" :loading="saving" @click="handleSave">
          {{ editingId ? '更新' : '保存' }}
        </t-button>
        <t-button v-if="editingId" variant="outline" @click="cancelEdit">
          取消
        </t-button>
      </div>
    </div>

    <!-- ═══ Memo List ═══ -->
    <div v-if="loading" class="flex justify-center py-8">
      <t-loading />
    </div>
    <div v-else-if="memos.length === 0" class="text-center text-gray-400 py-12">
      暂无投资备忘
    </div>
    <div v-else class="space-y-4">
      <div
        v-for="memo in memos"
        :key="memo.id"
        class="bg-white rounded-lg shadow-sm overflow-hidden"
      >
        <!-- Collapsed header -->
        <div
          class="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-gray-50 transition-colors"
          @click="toggleExpand(memo.id)"
        >
          <div class="flex items-center gap-3 min-w-0 flex-1">
            <span class="text-sm text-gray-400 shrink-0">{{ formatDate(memo.created_at) }}</span>
            <span class="font-medium truncate">{{ memo.title }}</span>
            <span @click.stop>
              <t-tag
                v-if="memo.stock_id"
                theme="primary"
                variant="light"
                size="small"
                style="cursor: pointer; flex-shrink: 0"
                @click="goStock(memo.stock_id)"
              >
                {{ getStockLabel(memo.stock_id) }}
              </t-tag>
            </span>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <t-button
              variant="text"
              size="small"
              @click.stop="handleEdit(memo)"
            >
              编辑
            </t-button>
            <t-popconfirm
              content="确定删除该备忘？"
              theme="danger"
              @confirm="handleDelete(memo.id)"
            >
              <t-button variant="text" size="small" theme="danger">删除</t-button>
            </t-popconfirm>
          </div>
        </div>

        <!-- Expanded content -->
        <div v-if="expandedId === memo.id" class="px-5 pb-4 border-t border-gray-100">
          <div class="prose prose-sm max-w-none mt-3 whitespace-pre-wrap text-gray-700 leading-relaxed">
            {{ expandedContents[memo.id] || '加载中...' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePortfolioStore } from '@/stores/portfolio'
import { MessagePlugin } from 'tdesign-vue-next'
import * as memosApi from '@/api/memos'
import type { InvestmentMemoListItem, InvestmentMemoCreate, InvestmentMemoUpdate } from '@/api/memos'

const router = useRouter()

const portfolioStore = usePortfolioStore()

const memos = ref<InvestmentMemoListItem[]>([])
const loading = ref(false)
const saving = ref(false)
const expandedId = ref<string | null>(null)
const editingId = ref<string | null>(null)
const expandedContents = ref<Record<string, string>>({})

const form = ref<{
  title: string
  content: string
  stock_id: string | null
}>({
  title: '',
  content: '',
  stock_id: null,
})

const stockOptions = computed(() => {
  return portfolioStore.stocks.map(s => ({
    label: `${s.symbol} - ${s.name || '加载中'}`,
    value: s.id,
  }))
})

function formatDate(d: string | null): string {
  if (!d) return ''
  const date = new Date(d)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function getStockLabel(stockId: string): string {
  const stock = portfolioStore.stocks.find(s => s.id === stockId)
  if (!stock) return '未知'
  return `${stock.name || stock.symbol}`
}

function goStock(stockId: string) {
  router.push(`/stock/${stockId}`)
}


function toggleExpand(id: string) {
  if (expandedId.value === id) {
    expandedId.value = null
    return
  }
  expandedId.value = id
  // Fetch full content if not already loaded
  if (!expandedContents.value[id]) {
    memosApi.getMemo(id).then(r => {
      if (r.ok) expandedContents.value[id] = r.data.content
    })
  }
}

async function fetchMemos() {
  loading.value = true
  const r = await memosApi.listMemos()
  if (r.ok) {
    memos.value = r.data
  }
  loading.value = false
}

async function handleSave() {
  if (!form.value.title.trim() || !form.value.content.trim()) {
    MessagePlugin.warning('标题和内容不能为空')
    return
  }

  saving.value = true
  if (editingId.value) {
    const data: InvestmentMemoUpdate = {
      title: form.value.title,
      content: form.value.content,
    }
    if (form.value.stock_id !== undefined) {
      data.stock_id = form.value.stock_id
    }
    const r = await memosApi.updateMemo(editingId.value, data)
    if (r.ok) {
      // 清除内容缓存，确保展开时重新拉取最新正文
      delete expandedContents.value[editingId.value]
      // 如果当前处于展开状态，立即刷新正文
      if (expandedId.value === editingId.value) {
        const memo = await memosApi.getMemo(editingId.value)
        if (memo.ok) expandedContents.value[editingId.value] = memo.data.content
      }
      MessagePlugin.success('备忘已更新')
    } else {
      MessagePlugin.error(r.error || '更新失败')
    }
  } else {
    const data: InvestmentMemoCreate = {
      title: form.value.title,
      content: form.value.content,
    }
    if (form.value.stock_id) {
      data.stock_id = form.value.stock_id
    }
    const r = await memosApi.createMemo(data)
    if (r.ok) {
      MessagePlugin.success('备忘已保存')
    } else {
      MessagePlugin.error(r.error || '保存失败')
    }
  }

  saving.value = false
  resetForm()
  await fetchMemos()
}

async function handleEdit(memo: InvestmentMemoListItem) {
  editingId.value = memo.id
  // Fetch full memo to get content
  const r = await memosApi.getMemo(memo.id)
  if (r.ok) {
    form.value.title = r.data.title
    form.value.content = r.data.content
    form.value.stock_id = r.data.stock_id
  } else {
    form.value.title = memo.title
    form.value.content = ''
    form.value.stock_id = memo.stock_id
  }
  // Scroll to editor
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelEdit() {
  resetForm()
}

function resetForm() {
  editingId.value = null
  form.value.title = ''
  form.value.content = ''
  form.value.stock_id = null
}

async function handleDelete(id: string) {
  const r = await memosApi.deleteMemo(id)
  if (r.ok) {
    MessagePlugin.success('备忘已删除')
    if (expandedId.value === id) expandedId.value = null
    await fetchMemos()
  } else {
    MessagePlugin.error(r.error || '删除失败')
  }
}

onMounted(async () => {
  if (portfolioStore.stocks.length === 0) {
    await portfolioStore.fetchAll()
  }
  await fetchMemos()
})
</script>

<style scoped>
.prose {
  font-size: 15px;
}
.prose img {
  max-width: 100%;
}
</style>
