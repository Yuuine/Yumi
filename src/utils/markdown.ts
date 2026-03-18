import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({
  breaks: true,
  gfm: true,
})

const ALLOWED_TAGS = [
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'p', 'br', 'hr',
  'strong', 'em', 'u', 's', 'del',
  'ul', 'ol', 'li',
  'blockquote', 'pre', 'code',
  'a', 'img',
  'table', 'thead', 'tbody', 'tr', 'th', 'td',
  'div', 'span',
]

const ALLOWED_ATTR = ['href', 'src', 'alt', 'title', 'class', 'id', 'target', 'rel']

/**
 * 将 Markdown 内容渲染为安全的 HTML
 * @param content - Markdown 格式的文本内容
 * @returns 经过 XSS 过滤的安全 HTML 字符串
 */
export function renderMarkdown(content: string): string {
  if (!content) return ''
  const rawHtml = marked.parse(content) as string
  return DOMPurify.sanitize(rawHtml, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
  })
}

/**
 * 将 Markdown 内容渲染为原始 HTML（未经过 XSS 过滤）
 * @param content - Markdown 格式的文本内容
 * @returns 原始 HTML 字符串
 */
export function renderMarkdownRaw(content: string): string {
  if (!content) return ''
  return marked.parse(content) as string
}

export { marked, DOMPurify }
