import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TagsInput from '@/components/common/TagsInput.vue'

describe('TagsInput', () => {
  it('renders correctly with default props', () => {
    const wrapper = mount(TagsInput, {
      props: {
        modelValue: '',
      },
    })
    expect(wrapper.find('.tags-input-wrapper').exists()).toBe(true)
  })

  it('respects placeholder prop', () => {
    const wrapper = mount(TagsInput, {
      props: {
        modelValue: '',
        placeholder: 'Enter tags',
      },
    })
    expect(wrapper.find('.tag-input').attributes('placeholder')).toBe('Enter tags')
  })

  it('can add a tag by pressing Enter', async () => {
    const wrapper = mount(TagsInput, {
      props: {
        modelValue: '',
      },
    })
    const input = wrapper.find('.tag-input')
    await input.setValue('newtag')
    await input.trigger('keydown.enter')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })
})
