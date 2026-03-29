import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AutoResizeTextarea from '@/components/common/AutoResizeTextarea.vue'

describe('AutoResizeTextarea', () => {
  it('renders correctly with default props', () => {
    const wrapper = mount(AutoResizeTextarea, {
      props: {
        modelValue: '',
      },
    })
    expect(wrapper.find('.auto-resize-textarea-wrapper').exists()).toBe(true)
  })

  it('emits update:modelValue when text changes', async () => {
    const wrapper = mount(AutoResizeTextarea, {
      props: {
        modelValue: '',
      },
    })
    const textarea = wrapper.find('.auto-resize-textarea')
    await textarea.setValue('New content')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['New content'])
  })

  it('respects placeholder prop', () => {
    const wrapper = mount(AutoResizeTextarea, {
      props: {
        modelValue: '',
        placeholder: 'Enter text here',
      },
    })
    expect(wrapper.find('.auto-resize-textarea').attributes('placeholder')).toBe('Enter text here')
  })
})
