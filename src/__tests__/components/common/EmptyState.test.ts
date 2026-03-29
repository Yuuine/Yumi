import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import EmptyState from '@/components/common/EmptyState.vue'
import { h, markRaw } from 'vue'

const MockIcon = markRaw({
  render: () => h('span', { class: 'mock-icon' }),
})

vi.mock('@/components/icons', () => ({
  IconError: { template: '<span data-test="icon-error"></span>' },
}))

describe('EmptyState', () => {
  it('renders correctly with default props', () => {
    const wrapper = mount(EmptyState)
    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.find('.empty-message').text()).toBe('暂无数据')
  })

  it('renders custom message when provided', () => {
    const wrapper = mount(EmptyState, {
      props: {
        message: '没有找到结果',
      },
    })
    expect(wrapper.find('.empty-message').text()).toBe('没有找到结果')
  })

  it('renders custom icon when provided', () => {
    const wrapper = mount(EmptyState, {
      props: {
        icon: MockIcon,
      },
    })
    expect(wrapper.find('.mock-icon').exists()).toBe(true)
  })

  it('renders slot content when provided', () => {
    const wrapper = mount(EmptyState, {
      slots: {
        default: '<button class="test-button">重试</button>',
      },
    })
    expect(wrapper.find('.test-button').text()).toBe('重试')
  })
})
