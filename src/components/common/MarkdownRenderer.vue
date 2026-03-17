<template>
  <div class="markdown-content" v-html="renderedContent"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'

interface Props {
  content: string
}

const props = defineProps<Props>()

marked.setOptions({
  breaks: true,
  gfm: true,
})

const renderedContent = computed(() => {
  if (!props.content) return ''
  return marked.parse(props.content) as string
})
</script>

<style lang="scss" scoped>
.markdown-content {
  font-size: 15px;
  line-height: 1.6;
  color: #333333;
  word-break: break-word;

  :deep(h1),
  :deep(h2),
  :deep(h3),
  :deep(h4),
  :deep(h5),
  :deep(h6) {
    margin: 16px 0 8px;
    font-weight: 600;
    line-height: 1.3;
    color: #1f2937;
  }

  :deep(h1) {
    font-size: 1.5em;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 8px;
  }

  :deep(h2) {
    font-size: 1.3em;
  }

  :deep(h3) {
    font-size: 1.15em;
  }

  :deep(p) {
    margin: 8px 0;
  }

  :deep(strong) {
    font-weight: 600;
    color: #1f2937;
  }

  :deep(em) {
    font-style: italic;
  }

  :deep(ul),
  :deep(ol) {
    margin: 8px 0;
    padding-left: 24px;
  }

  :deep(ul) {
    list-style-type: disc;
  }

  :deep(ol) {
    list-style-type: decimal;
  }

  :deep(li) {
    margin: 4px 0;
    line-height: 1.5;

    > ul,
    > ol {
      margin: 4px 0;
    }
  }

  :deep(code) {
    background: #f3f4f6;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
    font-size: 0.9em;
    color: #e11d48;
  }

  :deep(pre) {
    background: #1f2937;
    color: #e5e7eb;
    padding: 12px 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 12px 0;

    code {
      background: transparent;
      padding: 0;
      color: inherit;
      font-size: 13px;
      line-height: 1.5;
    }
  }

  :deep(blockquote) {
    margin: 12px 0;
    padding: 8px 16px;
    border-left: 4px solid #3b82f6;
    background: #eff6ff;
    color: #1e40af;
    border-radius: 0 4px 4px 0;

    p {
      margin: 4px 0;
    }
  }

  :deep(a) {
    color: #3b82f6;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  :deep(img) {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 8px 0;
  }

  :deep(hr) {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 16px 0;
  }

  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;

    th,
    td {
      border: 1px solid #e5e7eb;
      padding: 8px 12px;
      text-align: left;
    }

    th {
      background: #f9fafb;
      font-weight: 600;
    }

    tr:nth-child(even) {
      background: #f9fafb;
    }
  }
}
</style>
