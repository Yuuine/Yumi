import { describe, it, expect } from 'vitest'
import { renderMarkdown } from '@/utils/markdown'

describe('markdown - Markdown 渲染', () => {
  it('渲染空内容返回空字符串', () => {
    const result = renderMarkdown('')
    expect(result).toBe('')
  })

  it('渲染 null 返回空字符串', () => {
    const result = renderMarkdown(null as any)
    expect(result).toBe('')
  })

  it('渲染 undefined 返回空字符串', () => {
    const result = renderMarkdown(undefined as any)
    expect(result).toBe('')
  })

  it('渲染普通文本', () => {
    const result = renderMarkdown('Hello, world!')
    expect(result).toContain('Hello, world!')
    expect(result).toContain('<p>')
  })

  it('渲染粗体', () => {
    const result = renderMarkdown('**粗体文本**')
    expect(result).toContain('<strong>粗体文本</strong>')
  })

  it('渲染斜体', () => {
    const result = renderMarkdown('*斜体文本*')
    expect(result).toContain('<em>斜体文本</em>')
  })

  it('渲染删除线', () => {
    const result = renderMarkdown('~~删除线~~')
    expect(result).toContain('<del>删除线</del>')
  })

  it('渲染标题', () => {
    const result = renderMarkdown('# 一级标题')
    expect(result).toContain('<h1')
    expect(result).toContain('一级标题')
  })

  it('渲染多级标题', () => {
    const result = renderMarkdown('## 二级标题\n### 三级标题')
    expect(result).toContain('<h2')
    expect(result).toContain('<h3')
  })

  it('渲染链接', () => {
    const result = renderMarkdown('[示例链接](https://example.com)')
    expect(result).toContain('<a')
    expect(result).toContain('href="https://example.com"')
    expect(result).toContain('示例链接')
  })

  it('渲染图片', () => {
    const result = renderMarkdown('![示例图片](https://example.com/image.png)')
    expect(result).toContain('<img')
    expect(result).toContain('src="https://example.com/image.png"')
    expect(result).toContain('alt="示例图片"')
  })

  it('渲染无序列表', () => {
    const result = renderMarkdown('- 项目1\n- 项目2\n- 项目3')
    expect(result).toContain('<ul')
    expect(result).toContain('<li')
    expect(result).toContain('项目1')
    expect(result).toContain('项目2')
    expect(result).toContain('项目3')
  })

  it('渲染有序列表', () => {
    const result = renderMarkdown('1. 第一项\n2. 第二项\n3. 第三项')
    expect(result).toContain('<ol')
    expect(result).toContain('<li')
    expect(result).toContain('第一项')
    expect(result).toContain('第二项')
    expect(result).toContain('第三项')
  })

  it('渲染代码块', () => {
    const result = renderMarkdown('```\nconsole.log("Hello")\n```')
    expect(result).toContain('<pre')
    expect(result).toContain('<code')
    expect(result).toContain('console.log("Hello")')
  })

  it('渲染行内代码', () => {
    const result = renderMarkdown('使用 `code` 标签')
    expect(result).toContain('<code>code</code>')
  })

  it('渲染引用', () => {
    const result = renderMarkdown('> 这是一段引用')
    expect(result).toContain('<blockquote')
    expect(result).toContain('这是一段引用')
  })

  it('渲染分隔线', () => {
    const result = renderMarkdown('---')
    expect(result).toContain('<hr')
  })

  it('渲染表格', () => {
    const markdown = `
| 表头1 | 表头2 |
|-------|-------|
| 单元格1 | 单元格2 |
`
    const result = renderMarkdown(markdown)
    expect(result).toContain('<table')
    expect(result).toContain('<thead')
    expect(result).toContain('<tbody')
    expect(result).toContain('<tr')
    expect(result).toContain('<th')
    expect(result).toContain('<td')
  })

  it('XSS 防护 - 过滤 script 标签', () => {
    const result = renderMarkdown('<script>alert("XSS")</script>')
    expect(result).not.toContain('<script')
    expect(result).not.toContain('alert')
  })

  it('XSS 防护 - 过滤 style 标签', () => {
    const result = renderMarkdown('<style>body { color: red; }</style>')
    expect(result).not.toContain('<style')
  })

  it('XSS 防护 - 过滤 iframe 标签', () => {
    const result = renderMarkdown('<iframe src="https://evil.com"></iframe>')
    expect(result).not.toContain('<iframe')
  })

  it('XSS 防护 - 过滤 form 标签', () => {
    const result = renderMarkdown('<form action="https://evil.com"></form>')
    expect(result).not.toContain('<form')
  })

  it('XSS 防护 - 过滤 onload 事件', () => {
    const result = renderMarkdown('<img src="test.png" onload="alert(1)">')
    expect(result).not.toContain('onload')
  })

  it('XSS 防护 - 过滤 onerror 事件', () => {
    const result = renderMarkdown('<img src="test.png" onerror="alert(1)">')
    expect(result).not.toContain('onerror')
  })

  it('XSS 防护 - 过滤 onclick 事件', () => {
    const result = renderMarkdown('<button onclick="alert(1)">Click</button>')
    expect(result).not.toContain('onclick')
  })

  it('保留允许的标签', () => {
    const result = renderMarkdown('<p><strong>粗体</strong> <em>斜体</em></p>')
    expect(result).toContain('<p>')
    expect(result).toContain('<strong>粗体</strong>')
    expect(result).toContain('<em>斜体</em>')
  })

  it('渲染复杂内容', () => {
    const markdown = `
# 主要标题

这是一段**加粗文本**和*斜体文本*。

## 二级标题

- 列表项1
- 列表项2

[链接](https://example.com)

\`\`\`javascript
console.log("Hello, world!");
\`\`\`
`
    const result = renderMarkdown(markdown)
    expect(result).toContain('<h1')
    expect(result).toContain('<h2')
    expect(result).toContain('<strong')
    expect(result).toContain('<em')
    expect(result).toContain('<ul')
    expect(result).toContain('<li')
    expect(result).toContain('<a')
    expect(result).toContain('<pre')
    expect(result).toContain('<code')
  })
})
