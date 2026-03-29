import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import SettingsModal from '@/components/settings/SettingsModal.vue'
import { useSettingsStore } from '@/stores'

vi.mock('@/stores', () => ({
  useSettingsStore: vi.fn(),
}))

vi.mock('@/components/icons', () => ({
  IconClose: { template: '<span class="icon-close"></span>' },
  IconSettings: { template: '<span class="icon-settings"></span>' },
  IconUser: { template: '<span class="icon-user"></span>' },
}))

vi.mock('@/components/settings/AccountSettings.vue', () => ({
  default: { template: '<div class="account-settings-stub"></div>' },
}))

const mockSettingsStore = {
  showReasoning: false,
  verboseTest: false,
  setShowReasoning: vi.fn(),
  setVerboseTest: vi.fn(),
}

const defaultStubs = {
  Teleport: { template: '<div><slot /></div>' },
  Transition: { template: '<div><slot /></div>' },
  IconClose: true,
  IconSettings: true,
  IconUser: true,
  AccountSettings: true,
}

describe('SettingsModal', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()

    vi.mocked(useSettingsStore).mockReturnValue(mockSettingsStore as any)
  })

  it('renders when visible is true', () => {
    const wrapper = mount(SettingsModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs,
      },
    })

    expect(wrapper.find('.settings-modal-overlay').exists()).toBe(true)
    expect(wrapper.find('.settings-modal').exists()).toBe(true)
  })

  it('does not render when visible is false', () => {
    const wrapper = mount(SettingsModal, {
      props: { visible: false },
      global: {
        stubs: defaultStubs,
      },
    })

    expect(wrapper.find('.settings-modal-overlay').exists()).toBe(false)
  })

  it('renders modal title', () => {
    const wrapper = mount(SettingsModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs,
      },
    })

    expect(wrapper.find('.modal-title').text()).toBe('系统设置')
  })

  it('renders close button', () => {
    const wrapper = mount(SettingsModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs,
      },
    })

    expect(wrapper.find('.close-btn').exists()).toBe(true)
  })

  it('emits close event when close button is clicked', async () => {
    const wrapper = mount(SettingsModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs,
      },
    })

    await wrapper.find('.close-btn').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('renders tabs correctly', () => {
    const wrapper = mount(SettingsModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs,
      },
    })

    const tabs = wrapper.findAll('.tab-item')
    expect(tabs.length).toBe(2)
  })

  it('has general tab as active by default', () => {
    const wrapper = mount(SettingsModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs,
      },
    })

    const tabs = wrapper.findAll('.tab-item')
    expect(tabs[0].classes()).toContain('active')
  })

  it('renders settings tabs container', () => {
    const wrapper = mount(SettingsModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs,
      },
    })

    expect(wrapper.find('.settings-tabs').exists()).toBe(true)
  })

  it('renders settings content container', () => {
    const wrapper = mount(SettingsModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs,
      },
    })

    expect(wrapper.find('.settings-content').exists()).toBe(true)
  })

  it('renders modal body', () => {
    const wrapper = mount(SettingsModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs,
      },
    })

    expect(wrapper.find('.modal-body').exists()).toBe(true)
  })

  it('renders settings layout', () => {
    const wrapper = mount(SettingsModal, {
      props: { visible: true },
      global: {
        stubs: defaultStubs,
      },
    })

    expect(wrapper.find('.settings-layout').exists()).toBe(true)
  })
})
