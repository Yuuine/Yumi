import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ModalWrapper from '@/components/common/ModalWrapper.vue'

describe('ModalWrapper', () => {
  const defaultStubs = {
    Teleport: { template: '<div><slot /></div>' },
    Transition: { template: '<div><slot /></div>' },
    IconClose: true,
  }

  it('renders correctly with visible prop true', () => {
    const wrapper = mount(ModalWrapper, {
      props: {
        visible: true,
      },
      global: {
        stubs: defaultStubs,
      },
    })
    expect(wrapper.find('.modal-wrapper-overlay').exists()).toBe(true)
    expect(wrapper.find('.modal-wrapper-container').exists()).toBe(true)
  })

  it('does not render when visible prop is false', () => {
    const wrapper = mount(ModalWrapper, {
      props: {
        visible: false,
      },
      global: {
        stubs: defaultStubs,
      },
    })
    expect(wrapper.find('.modal-wrapper-overlay').exists()).toBe(false)
  })

  it('renders title when provided', () => {
    const wrapper = mount(ModalWrapper, {
      props: {
        visible: true,
        title: 'Test Title',
      },
      global: {
        stubs: defaultStubs,
      },
    })
    expect(wrapper.find('.modal-wrapper-title').text()).toBe('Test Title')
  })

  it('applies correct size classes', () => {
    const wrapper = mount(ModalWrapper, {
      props: {
        visible: true,
        size: 'large',
      },
      global: {
        stubs: defaultStubs,
      },
    })
    expect(wrapper.find('.modal-wrapper-container').classes()).toContain('modal-wrapper-large')
  })

  it('applies custom class when provided', () => {
    const wrapper = mount(ModalWrapper, {
      props: {
        visible: true,
        customClass: 'custom-modal-class',
      },
      global: {
        stubs: defaultStubs,
      },
    })
    expect(wrapper.find('.modal-wrapper-container').classes()).toContain('custom-modal-class')
  })

  it.skip('emits close event when close button is clicked', async () => {
    const wrapper = mount(ModalWrapper, {
      props: {
        visible: true,
        showClose: true,
      },
      global: {
        stubs: defaultStubs,
      },
    })
    const closeButton = wrapper.find('.modal-wrapper-close')
    expect(closeButton.exists()).toBe(true)
    await closeButton.trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('renders slot content correctly', () => {
    const wrapper = mount(ModalWrapper, {
      props: {
        visible: true,
      },
      slots: {
        default: '<div class="test-content">Test Content</div>',
      },
      global: {
        stubs: defaultStubs,
      },
    })
    expect(wrapper.find('.test-content').text()).toBe('Test Content')
  })
})
