import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import TestResultDialog from '@/components/Models/TestResultDialog.vue'
import type { ModelTestResponse } from '@/types'

vi.mock('@/components/common/MarkdownRenderer.vue', () => ({
  default: { template: '<div class="markdown-renderer-stub"></div>' },
}))

vi.mock('@/components/icons', () => ({
  IconClose: { template: '<span data-test="icon-close"></span>' },
  IconSuccess: { template: '<span data-test="icon-success"></span>' },
  IconError: { template: '<span data-test="icon-error"></span>' },
  IconInfo: { template: '<span data-test="icon-info"></span>' },
}))

const mockSuccessResult: ModelTestResponse = {
  success: true,
  message: '测试成功',
  response: 'This is a test response',
  reasoning: 'This is the reasoning process',
  latency: 1.234,
}

const mockErrorResult: ModelTestResponse = {
  success: false,
  message: '测试失败',
  response: '',
  reasoning: '',
  latency: 0,
}

describe('TestResultDialog - 测试结果对话框', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('当 visible 为 true 时渲染对话框', () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.find('.test-dialog-overlay').exists()).toBe(true)
    })

    it('渲染对话框标题', () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.find('h3').text()).toBe('测试结果')
    })

    it('渲染关闭按钮', () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.find('.close-btn').exists()).toBe(true)
    })

    it('渲染确定按钮', () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.find('.dialog-btn').exists()).toBe(true)
      expect(wrapper.text()).toContain('确定')
    })
  })

  describe('Props', () => {
    it('接受 visible prop', () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.props('visible')).toBe(true)
    })

    it('接受 result prop', () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.props('result')).toEqual(mockSuccessResult)
    })
  })

  describe('Emits', () => {
    it('有正确的 emit 定义', () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(typeof wrapper.vm.$emit).toBe('function')
    })

    it('点击关闭按钮时触发 close event', async () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      await wrapper.find('.close-btn').trigger('click')
      expect(wrapper.emitted('close')).toHaveLength(1)
    })

    it('点击确定按钮时触发 close event', async () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      await wrapper.find('.dialog-btn').trigger('click')
      expect(wrapper.emitted('close')).toHaveLength(1)
    })

    it('点击遮罩层时触发 close event', async () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      await wrapper.find('.test-dialog-overlay').trigger('click')
      expect(wrapper.emitted('close')).toHaveLength(1)
    })
  })

  describe('测试结果显示', () => {
    it('显示成功状态时的正确样式和消息', () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.find('.test-status').classes()).toContain('success')
      expect(wrapper.text()).toContain('连接成功')
    })

    it('显示错误状态时的正确样式和消息', () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockErrorResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.find('.test-status').classes()).toContain('error')
      expect(wrapper.text()).toContain('测试失败')
    })

    it('显示响应时间', () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.find('.test-latency').exists()).toBe(true)
      expect(wrapper.text()).toContain('响应时间')
    })

    it('显示推理过程', () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.find('.test-reasoning').exists()).toBe(true)
      expect(wrapper.text()).toContain('推理过程')
    })

    it('显示模型响应', () => {
      const wrapper = mount(TestResultDialog, {
        props: {
          visible: true,
          result: mockSuccessResult,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.find('.test-response').exists()).toBe(true)
      expect(wrapper.text()).toContain('模型响应')
    })
  })
})
