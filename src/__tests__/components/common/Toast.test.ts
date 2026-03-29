import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Toast from '@/components/common/Toast.vue'
import { ref } from 'vue'

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    visible: ref(true),
    message: ref('Test message'),
    type: ref('success'),
    hide: vi.fn(),
  })
}))

vi.mock('@/components/icons', () => ({
  IconSuccess: { template: '<span data-test="icon-success"></span>' },
  IconError: { template: '<span data-test="icon-error"></span>' },
  IconWarning: { template: '<span data-test="icon-warning"></span>' },
  IconInfo: { template: '<span data-test="icon-info"></span>' }
}))

describe('Toast', () => {
  it('renders correctly when visible', () => {
    const wrapper = mount(Toast, {
      global: {
        stubs: {
          Teleport: { template: '<div><slot /></div>' },
          Transition: { template: '<div><slot /></div>' }
        }
      }
    })
    expect(wrapper.find('.toast-container').exists()).toBe(true)
    expect(wrapper.find('.toast-message').text()).toBe('Test message')
  })

  it('applies correct type class', () => {
    const wrapper = mount(Toast, {
      global: {
        stubs: {
          Teleport: { template: '<div><slot /></div>' },
          Transition: { template: '<div><slot /></div>' }
        }
      }
    })
    expect(wrapper.find('.toast-container').classes()).toContain('toast-success')
  })

  it('renders the icon based on type', () => {
    const wrapper = mount(Toast, {
      global: {
        stubs: {
          Teleport: { template: '<div><slot /></div>' },
          Transition: { template: '<div><slot /></div>' }
        }
      }
    })
    expect(wrapper.find('[data-test="icon-success"]').exists()).toBe(true)
  })
})
