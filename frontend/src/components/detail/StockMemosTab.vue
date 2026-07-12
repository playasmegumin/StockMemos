<template>
  <div>
    <!-- Top editor -->
    <div class="bg-white rounded-lg p-4 mb-4 border border-gray-100">
      <div class="text-sm font-medium text-gray-500 mb-3">
        {{ editingId ? '编辑备忘' : '新建备忘' }}
      </div>
      <div class="mb-3">
        <t-input
          v-model="form.title"
          placeholder="标题"
          size="medium"
          maxlength="200"
          clearable
        />
      </div>
      <div class="mb-3">
        <t-textarea
          v-model="form.content"
          placeholder="写下关于这只股票的投资思考…"
          :autosize="{ minRows: 3, maxRows: 8 }"
          style="font-size: 16px; line-height: 1.6"
        />
      </div>
      <div class="flex gap-2">
        <t-button
          theme="primary"
          size="small"
          :loading="saving"
          @click="handleSave"
        >
          {{ editingId ? '更新' : '保存备忘' }}
        </t-button>
        <t-button
          v-if="editingId"
          variant="outline"
          size="small"
          @click="cancelEdit"
        >
          取消
        </t-button>
      </div>
    </div>

    <!-- Memo list -->
    <div v-if="loading" class="flex justify-center py-4"><t-loading /></div>
    <div v-else-if="memos.length === 0" class="text-center text-gray-400 py-6">
      暂无关联个股的投资备忘
    </div>
    <div v-else class="space-y-3">
      <div
        v-for="memo in memos"
        :key="memo.id"
        class="border border-gray-100 rounded-lg overflow-hidden"
      >
        <div
          class="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50"
          @click="toggleExpand(memo.id)"
        >
          <div class="flex items-center gap-3">
            <span class="text-xs text-gray-400">{{ formatDate(memo.created_at) }}</span>
            <span class="text-sm font-medium">{{ memo.title }}</span>
          </div>
          <div class="flex items-center gap-1" @click.stop>
            <t-button variant="text" size="small" @click="handleEdit(memo.id)">编辑</t-button>
            <t-popconfirm
              content="确定删除该备忘？"
              theme="danger"
              @confirm="handleDelete(memo.id)"
            >
              <t-button variant="text" size="small" theme="danger">删除</t-button>
            </t-popconfirm>
          </div>
        </div>
        <div v-if="expandedId === memo.id" class="px-4 pb-3 border-t border-gray-100">
          <div class="mt-2 text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
            {{ expandedContent }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import * as memosApi from '@/api/memos'
import type { InvestmentMemoListItem } from '@/api/memos'

const props = defineProps<{
  stockId: string
}>()

const memos = ref<InvestmentMemoListItem[]>([])
const loading = ref(false)
const saving = ref(false)
const expandedId = ref<string | null>(null)
const expandedContent = ref('')
const editingId = ref<string | null>(null)

const form = ref({ title: '', content: '' })

function formatDate(d: string | null): string {
  if (!d) return ''
  const date = new Date(d)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

async function toggleExpand(id: string) {
  if (expandedId.value === id) {
    expandedId.value = null
    expandedContent.value = ''
    return
  }
  expandedId.value = id
  expandedContent.value = ''
  const r = await memosApi.getMemo(id)
  if (r.ok) {
    expandedContent.value = r.data.content
  }
}

async function fetchMemos() {
  loading.value = true
  const r = await memosApi.listMemos(props.stockId)
  if (r.ok) {
    memos.value = r.data
  }
  loading.value = false
}

function handleEdit(id: string) {
  editingId.value = id
  // Fetch full memo to backfill form
  memosApi.getMemo(id).then(r => {
    if (r.ok) {
      form.value.title = r.data.title
      form.value.content = r.data.content
    }
  })
}

function cancelEdit() {
  editingId.value = null
  form.value.title = ''
  form.value.content = ''
}

async function handleSave() {
  if (!form.value.title.trim() || !form.value.content.trim()) {
    MessagePlugin.warning('标题和内容不能为空')
    return
  }
  saving.value = true

  if (editingId.value) {
    // Update existing
    const r = await memosApi.updateMemo(editingId.value, {
      title: form.value.title,
      content: form.value.content,
    })
    if (r.ok) {
      // If currently expanded, refresh expanded content
      if (expandedId.value === editingId.value) {
        expandedContent.value = form.value.content
      }
      MessagePlugin.success('备忘已更新')
    } else {
      MessagePlugin.error(r.error || '更新失败')
    }
  } else {
    // Create new
    const r = await memosApi.createMemo({
      title: form.value.title,
      content: form.value.content,
      stock_id: props.stockId,
    })
    if (r.ok) {
      MessagePlugin.success('备忘已保存')
    } else {
      MessagePlugin.error(r.error || '保存失败')
    }
  }

  saving.value = false
  form.value.title = ''
  form.value.content = ''
  editingId.value = null
  await fetchMemos()
}

async function handleDelete(id: string) {
  const r = await memosApi.deleteMemo(id)
  if (r.ok) {
    MessagePlugin.success('备忘已删除')
    if (expandedId.value === id) {
      expandedId.value = null
      expandedContent.value = ''
    }
    await fetchMemos()
  } else {
    MessagePlugin.error(r.error || '删除失败')
  }
}

watch(() => props.stockId, () => { fetchMemos() })

onMounted(() => { fetchMemos() })
</script>
