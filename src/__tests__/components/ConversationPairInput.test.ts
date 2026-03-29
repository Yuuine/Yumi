import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ConversationPairInput from '@/components/common/ConversationPairInput.vue'

describe('ConversationPairInput', () => {
  it('renders correctly with default props', () => {
    const wrapper = mount(ConversationPairInput, {
      props: {
        modelValue: '',
      },
    })
    expect(wrapper.find('.conversation-pair-input-wrapper').exists()).toBe(true)
  })
})
