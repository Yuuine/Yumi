import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatMessage from '@/components/ChatMessage.vue'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    profile: {
      roleName: 'Yumi',
    },
  }),
}))

describe('ChatMessage', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders user message correctly', () => {
    const wrapper = mount(ChatMessage, {
      props: {
        message: {
          id: '1',
          role: 'user',
          content: 'Hello, this is a test message',
          timestamp: '2024-01-01T12:00:00Z',
        },
      },
    })

    expect(wrapper.find('.chat-message.user').exists()).toBe(true)
    expect(wrapper.text()).toContain('Hello, this is a test message')
  })

  it('renders assistant message correctly', () => {
    const wrapper = mount(ChatMessage, {
      props: {
        message: {
          id: '2',
          role: 'assistant',
          content: 'Hello! How can I help you?',
          timestamp: '2024-01-01T12:00:01Z',
        },
      },
    })

    expect(wrapper.find('.chat-message.assistant').exists()).toBe(true)
    expect(wrapper.text()).toContain('Hello! How can I help you?')
  })

  it('renders emotion badge when present', () => {
    const wrapper = mount(ChatMessage, {
      props: {
        message: {
          id: '3',
          role: 'assistant',
          content: 'I am happy!',
          timestamp: '2024-01-01T12:00:02Z',
          emotion: { valence: 0.8, arousal: 0.6 },
        },
      },
    })

    expect(wrapper.find('.message-emotion').exists()).toBe(true)
  })

  it('does not render emotion badge when absent', () => {
    const wrapper = mount(ChatMessage, {
      props: {
        message: {
          id: '4',
          role: 'user',
          content: 'No emotion here',
          timestamp: '2024-01-01T12:00:03Z',
        },
      },
    })

    expect(wrapper.find('.message-emotion').exists()).toBe(false)
  })

  it('formats timestamp correctly', () => {
    const wrapper = mount(ChatMessage, {
      props: {
        message: {
          id: '5',
          role: 'user',
          content: 'Test',
          timestamp: '2024-01-15T08:30:00Z',
        },
      },
    })

    const timeElement = wrapper.find('.message-time')
    expect(timeElement.exists()).toBe(true)
  })

  it('renders long message content', () => {
    const longContent = 'A'.repeat(500)
    const wrapper = mount(ChatMessage, {
      props: {
        message: {
          id: '6',
          role: 'assistant',
          content: longContent,
          timestamp: '2024-01-01T12:00:00Z',
        },
      },
    })

    expect(wrapper.text()).toContain(longContent)
  })
})
