import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ModelsModal from '@/components/Models/ModelsModal.vue'

vi.mock('@/stores', () => ({
  useModelsStore: vi.fn(() => ({
    models: [],
    isLoading: false,
    isTesting: false,
    testResult: null,
    loadModels: vi.fn(),
    disableModel: vi.fn(),
    enableModel: vi.fn(),
    deleteModelSilent: vi.fn(),
    testModelById: vi.fn(),
    updateModelSilent: vi.fn(),
    createModelSilent: vi.fn(),
  })),
  useSettingsStore: vi.fn(() => ({
    verboseTest: false,
  })),
}))

vi.mock('@/composables', () => ({
  useToast: vi.fn(() => ({
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn(),
  })),
  useConfirmDialog: vi.fn(() => ({
    showDialog: vi.fn(),
  })),
}))

vi.mock('@/components/Models/ModelCard.vue', () => ({
  default: { template: '<div class="model-card-stub"></div>' },
}))

vi.mock('@/components/Models/ModelForm.vue', () => ({
  default: { template: '<div class="model-form-stub"></div>' },
}))

vi.mock('@/components/Models/TestResultDialog.vue', () => ({
  default: { template: '<div class="test-result-dialog-stub"></div>' },
}))

vi.mock('@/components/common/LoadingState.vue', () => ({
  default: { template: '<div class="loading-state-stub"></div>' },
}))

vi.mock('@/components/common/Toast.vue', () => ({
  default: { template: '<div class="toast-stub"></div>' },
}))

vi.mock('@/components/icons', () => ({
  IconClose: { template: '<span data-test="icon-close"></span>' },
  IconError: { template: '<span data-test="icon-error"></span>' },
  IconAdd: { template: '<span data-test="icon-add"></span>' },
}))

describe('ModelsModal - 模型管理模态框', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('基础渲染', () => {
    it('当 visible 为 true 时渲染模态框', () => {
      const wrapper = mount(ModelsModal, {
        props: {
          visible: true,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.find('.models-modal-overlay').exists()).toBe(true)
    })

    it('渲染模态框标题', () => {
      const wrapper = mount(ModelsModal, {
        props: {
          visible: true,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.find('.modal-title').text()).toBe('模型管理')
    })

    it('渲染添加按钮', () => {
      const wrapper = mount(ModelsModal, {
        props: {
          visible: true,
        },
        global: {
          stubs: {
            Teleport: { template: '<div><slot /></div>' },
            Transition: { template: '<div><slot /></div>' },
          },
        },
      })
      expect(wrapper.find('.add-btn').exists()).toBe(true)
      expect(wrapper.text()).toContain('添加')
    })

    it('渲染关闭按钮', () => {
      const wrapper = mount(ModelsModal, {
        props: {
          visible: true,
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
  })

  describe('Props', () => {
    it('接受 visible prop', () => {
      const wrapper = mount(ModelsModal, {
        props: {
          visible: true,
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
  })

  describe('Emits', () => {
    it('有正确的 emit 定义', () => {
      const wrapper = mount(ModelsModal, {
        props: {
          visible: true,
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
  })
})
