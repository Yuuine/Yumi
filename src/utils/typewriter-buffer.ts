/**
 * 字符缓存渲染器
 *
 * 功能说明：
 * - 设立字符缓存窗口，持续接收并累积字符
 * - 当缓存字符数达到预设阈值时，开始启动渲染
 * - 渲染启动后，采用边接收新字符、边渲染已缓存字符的方式
 * - 动态维护缓存窗口，使其始终保持大致稳定的字符存量
 * - 渲染过程保持匀速，不受后端数据到达快慢影响
 */

export interface TypewriterBufferConfig {
  /**
   * 缓存阈值（字符数），达到此阈值后开始渲染
   * @default 20
   */
  bufferThreshold: number

  /**
   * 渲染速度（字符/秒）
   * @default 30
   */
  charsPerSecond: number
}

const DEFAULT_CONFIG: TypewriterBufferConfig = {
  bufferThreshold: 20,
  charsPerSecond: 30,
}

export class TypewriterBuffer {
  private config: TypewriterBufferConfig

  /**
   * 待渲染的字符缓冲区
   */
  private buffer: string = ''

  /**
   * 已渲染的完整文本
   */
  private renderedText: string = ''

  /**
   * 是否已开始渲染
   */
  private isRendering: boolean = false

  /**
   * 是否已完成（流结束且缓冲区为空）
   */
  private isFinished: boolean = false

  /**
   * requestAnimationFrame 的 ID
   */
  private animationFrameId: number | null = null

  /**
   * 上一次渲染的时间戳
   */
  private lastRenderTime: number = 0

  /**
   * 渲染回调函数
   */
  private onRenderCallback: ((text: string) => void) | null = null

  /**
   * 完成回调函数
   */
  private onFinishCallback: (() => void) | null = null

  /**
   * 进度回调函数
   */
  private onProgressCallback: ((renderedText: string, bufferLength: number) => void) | null = null

  constructor(config?: Partial<TypewriterBufferConfig>) {
    this.config = { ...DEFAULT_CONFIG, ...config }
  }

  /**
   * 设置渲染回调函数
   * 当有新字符需要渲染时调用
   */
  onRender(callback: (text: string) => void): void {
    this.onRenderCallback = callback
  }

  /**
   * 设置完成回调函数
   * 当所有字符都渲染完成时调用
   */
  onFinish(callback: () => void): void {
    this.onFinishCallback = callback
  }

  /**
   * 设置进度回调函数
   * 每次渲染字符后调用
   */
  onProgress(callback: (renderedText: string, bufferLength: number) => void): void {
    this.onProgressCallback = callback
  }

  /**
   * 推入新字符到缓冲区
   */
  pushCharacters(chars: string): void {
    if (this.isFinished) {
      return
    }

    this.buffer += chars

    // 如果还没开始渲染，检查是否达到阈值
    if (!this.isRendering) {
      if (this.buffer.length >= this.config.bufferThreshold) {
        this.startRendering()
      }
    }
  }

  /**
   * 标记流已结束
   * 即使缓冲区没达到阈值，也会开始渲染剩余字符
   */
  endStream(): void {
    this.isFinished = true

    // 如果还有未渲染的字符，确保它们被渲染
    if (this.buffer.length > 0 && !this.isRendering) {
      this.startRendering()
    }
  }

  /**
   * 开始渲染循环
   */
  private startRendering(): void {
    if (this.isRendering) {
      return
    }

    this.isRendering = true
    this.lastRenderTime = performance.now()
    this.scheduleRender()
  }

  /**
   * 调度下一次渲染
   */
  private scheduleRender(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId)
    }

    this.animationFrameId = requestAnimationFrame(timestamp => this.render(timestamp))
  }

  /**
   * 执行渲染
   */
  private render(currentTime: number): void {
    const deltaTime = currentTime - this.lastRenderTime
    this.lastRenderTime = currentTime

    // 计算本次应该渲染的字符数
    // 使用 Math.max 确保至少渲染 1 个字符（如果有字符待渲染）
    let charsToRender = Math.floor((deltaTime / 1000) * this.config.charsPerSecond)

    // 关键修复：确保每次至少渲染 1 个字符（如果有字符待渲染）
    if (charsToRender === 0 && this.buffer.length > 0) {
      charsToRender = 1
    }

    if (charsToRender > 0 && this.buffer.length > 0) {
      // 从缓冲区取出字符
      const chars = this.buffer.slice(0, charsToRender)
      this.buffer = this.buffer.slice(charsToRender)

      // 追加到已渲染文本
      this.renderedText += chars

      // 调用渲染回调
      if (this.onRenderCallback) {
        this.onRenderCallback(this.renderedText)
      }

      // 调用进度回调
      if (this.onProgressCallback) {
        this.onProgressCallback(this.renderedText, this.buffer.length)
      }
    }

    // 检查是否还有字符需要渲染
    if (this.buffer.length > 0 || !this.isFinished) {
      // 继续调度下一次渲染
      this.scheduleRender()
    } else {
      // 所有字符都渲染完成
      this.isRendering = false
      this.animationFrameId = null

      if (this.onFinishCallback) {
        this.onFinishCallback()
      }
    }
  }

  /**
   * 停止渲染并清理资源
   */
  stop(): void {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId)
      this.animationFrameId = null
    }

    this.isRendering = false
    this.onRenderCallback = null
    this.onFinishCallback = null
    this.onProgressCallback = null
  }

  /**
   * 获取当前已渲染的文本
   */
  getRenderedText(): string {
    return this.renderedText
  }

  /**
   * 获取缓冲区中剩余的字符数
   */
  getBufferLength(): number {
    return this.buffer.length
  }

  /**
   * 检查是否正在渲染
   */
  getIsRendering(): boolean {
    return this.isRendering
  }

  /**
   * 检查是否已完成
   */
  getIsFinished(): boolean {
    return this.isFinished && this.buffer.length === 0 && !this.isRendering
  }
}

/**
 * 创建一个字符缓存渲染器实例
 */
export function createTypewriterBuffer(config?: Partial<TypewriterBufferConfig>): TypewriterBuffer {
  return new TypewriterBuffer(config)
}
