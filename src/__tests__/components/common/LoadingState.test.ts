import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoadingState from '@/components/common/LoadingState.vue'

describe('LoadingState', () => {
  it('renders correctly with visible prop true', () => {
    const wrapper = mount(LoadingState, {
      props: {
        visible: true,
      },
      global: {
        stubs: {
          Teleport: { template: '<div><slot /></div>' },
          Transition: { template: '<div><slot /></div>' }
        }
      }
    })
    expect(wrapper.find('.loading-overlay').exists()).toBe(true)
    expect(wrapper.find('.loading-content').exists()).toBe(true)
    expect(wrapper.find('.loading-spinner').exists()).toBe(true)
  })

  it('does not render when visible prop is false', () => {
    const wrapper = mount(LoadingState, {
      props: {
        visible: false,
      },
      global: {
        stubs: {
          Teleport: { template: '<div><slot /></div>' },
          Transition: { template: '<div><slot /></div>' }
        }
      }
    })
    expect(wrapper.find('.loading-overlay').exists()).toBe(false)
  })

  it('renders default text when visible', () => {
    const wrapper = mount(LoadingState, {
      props: {
        visible: true,
      },
      global: {
        stubs: {
          Teleport: { template: '<div><slot /></div>' },
          Transition: { template: '<div><slot /></div>' }
        }
      }
    })
    expect(wrapper.find('.loading-text').text()).toBe('加载中...')
  })

  it('renders custom text when provided', () => {
    const wrapper = mount(LoadingState, {
      props: {
        visible: true,
        text: '正在处理...',
      },
      global: {
        stubs: {
          Teleport: { template: '<div><slot /></div>' },
          Transition: { template: '<div><slot /></div>' }
        }
      }
    })
    expect(wrapper.find('.loading-text').text()).toBe('正在处理...')
  })

  it('does not show text when text prop is empty', () => {
    const wrapper = mount(LoadingState, {
      props: {
        visible: true,
        text: '',
      },
      global: {
        stubs: {
          Teleport: { template: '<div><slot /></div>' },
          Transition: { template: '<div><slot /></div>' }
        }
      }
    })
    expect(wrapper.find('.loading-text').exists()).toBe(false)
  })
})
