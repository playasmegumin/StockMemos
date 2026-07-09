<template>
  <div class="report-list">
    <!-- Inline add form -->
    <div v-if="showForm" class="mb-4 border rounded-lg p-4 bg-gray-50 space-y-3">
      <t-input v-model="form.title" placeholder="报告标题" />
      <t-textarea v-model="form.content" placeholder="报告内容" :rows="4" />
      <div class="flex gap-2">
        <t-button theme="primary" size="small" @click="handleAdd" :loading="submitting">确认</t-button>
        <t-button variant="outline" size="small" @click="closeForm">取消</t-button>
      </div>
    </div>
    <t-button v-else size="small" variant="outline" @click="openForm" class="mb-3">添加报告</t-button>

    <!-- Report list -->
    <div v-if="stockStore.reports.length === 0" class="text-sm text-gray-400 py-4 text-center">
      暂无分析报告
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="report in stockStore.reports"
        :key="report.id"
        class="border rounded-lg overflow-hidden"
      >
        <div
          class="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors"
          @click="toggleReport(report.id)"
        >
          <div class="flex-1 min-w-0">
            <div class="font-medium text-sm truncate">{{ report.title }}</div>
            <div class="text-xs text-gray-400 mt-0.5">{{ fmtTime(report.generated_at) }}</div>
          </div>
          <t-icon
            :name="expandedReports.has(report.id) ? 'chevron-up' : 'chevron-down'"
            class="text-gray-400 ml-2"
          />
        </div>

        <!-- Expanded content -->
        <div v-if="expandedReports.has(report.id)" class="px-4 pb-3">
          <t-divider class="my-1" />
          <div class="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">{{ report.content }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useStockStore } from '@/stores/stock'
import { fmtTime } from '@/utils/format'
import { MessagePlugin } from 'tdesign-vue-next'

const stockStore = useStockStore()
const expandedReports = ref(new Set<string>())
const showForm = ref(false)
const submitting = ref(false)

const form = reactive({
  title: '',
  content: '',
})

function toggleReport(id: string) {
  if (expandedReports.value.has(id)) {
    expandedReports.value.delete(id)
  } else {
    expandedReports.value.add(id)
  }
}

function openForm() {
  form.title = ''
  form.content = ''
  showForm.value = true
}

function closeForm() {
  showForm.value = false
}

async function handleAdd() {
  if (!form.title.trim()) {
    MessagePlugin.warning('请输入报告标题')
    return
  }
  if (!form.content.trim()) {
    MessagePlugin.warning('请输入报告内容')
    return
  }

  submitting.value = true
  const r = await stockStore.addReport({
    title: form.title.trim(),
    content: form.content.trim(),
    generated_at: new Date().toISOString(),
  })
  if (r.ok) {
    MessagePlugin.success('报告已添加')
    closeForm()
  } else {
    MessagePlugin.error(r.error || '添加失败')
  }
  submitting.value = false
}
</script>
