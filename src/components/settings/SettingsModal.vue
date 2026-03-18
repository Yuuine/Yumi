<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="settings-modal-overlay" @click.self="handleClose">
        <div class="settings-modal">
          <div class="modal-header">
            <h2 class="modal-title">设置</h2>
            <button class="close-btn" @click="handleClose" aria-label="关闭">
              <IconClose />
            </button>
          </div>

          <div class="modal-body">
            <div class="settings-layout">
              <div class="settings-tabs">
                <button
                  v-for="tab in tabs"
                  :key="tab.id"
                  class="tab-item"
                  :class="{ active: activeTab === tab.id }"
                  @click="activeTab = tab.id"
                >
                  <component :is="tab.icon" class="tab-icon" />
                  <span class="tab-label">{{ tab.label }}</span>
                </button>
              </div>

              <div class="settings-content">
                <div v-if="activeTab === 'general'" class="settings-panel">
                  <div class="panel-title">通用设置</div>

                  <div class="settings-section">
                    <div class="setting-item">
                      <div class="setting-info">
                        <div class="setting-label">推理过程显示</div>
                        <div class="setting-description">
                          开启后，若当前模型支持推理，将在对话中显示思考过程
                        </div>
                      </div>
                      <div class="setting-control">
                        <button
                          class="toggle-switch"
                          :class="{ active: settingsStore.showReasoning }"
                          @click="handleToggleReasoning"
                        >
                          <span class="toggle-knob"></span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-else-if="activeTab === 'chat'" class="settings-panel">
                  <div class="panel-title">聊天设置</div>

                  <div class="settings-section">
                    <div class="setting-item">
                      <div class="setting-info">
                        <div class="setting-label">详细测试信息</div>
                        <div class="setting-description">
                          开启后，测试模型连通性时将显示完整的模型响应信息
                        </div>
                      </div>
                      <div class="setting-control">
                        <button
                          class="toggle-switch"
                          :class="{ active: settingsStore.verboseTest }"
                          @click="handleToggleVerboseTest"
                        >
                          <span class="toggle-knob"></span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-else-if="activeTab === 'appearance'" class="settings-panel">
                  <div class="panel-title">外观设置</div>
                  <div class="settings-placeholder">
                    <IconInfo class="placeholder-icon" />
                    <span>外观设置功能开发中...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, markRaw } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { IconClose, IconInfo, IconChat, IconModels } from '@/components/icons'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const settingsStore = useSettingsStore()

const activeTab = ref('general')

const tabs = [
  {
    id: 'general',
    label: '通用设置',
    icon: markRaw(IconModels),
  },
  {
    id: 'chat',
    label: '聊天设置',
    icon: markRaw(IconChat),
  },
  {
    id: 'appearance',
    label: '外观设置',
    icon: markRaw(IconInfo),
  },
]

function handleToggleReasoning() {
  settingsStore.setShowReasoning(!settingsStore.showReasoning)
}

function handleToggleVerboseTest() {
  settingsStore.setVerboseTest(!settingsStore.verboseTest)
}

function handleClose() {
  emit('close')
}
</script>

<style lang="scss" scoped>
.settings-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.settings-modal {
  position: relative;
  background: #ffffff;
  border-radius: 12px;
  width: 600px;
  max-width: 80vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;

  .modal-title {
    margin: 0;
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: #333333;
  }
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #9ca3af;
  transition: all 0.2s;

  &:hover {
    background: #f3f4f6;
    color: #333333;
  }

  svg {
    width: 20px;
    height: 20px;
  }
}

.modal-body {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.settings-layout {
  display: flex;
  height: 100%;
  min-height: 400px;
}

.settings-tabs {
  width: 160px;
  padding: 16px 8px;
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
  color: #666666;

  &:hover {
    background: #f3f4f6;
    color: #333333;
  }

  &.active {
    background: #ffffff;
    color: #3b82f6;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
}

.tab-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.tab-label {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
}

.settings-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.settings-panel {
  .panel-title {
    font-size: var(--font-size-lg);
    font-weight: 600;
    color: #333333;
    margin-bottom: 20px;
  }
}

.settings-section {
  margin-bottom: 24px;

  .section-title {
    font-size: 13px;
    font-weight: 600;
    color: #333333;
    margin-bottom: 12px;
    line-height: 20px;
  }
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.setting-info {
  flex: 1;
  min-width: 0;
}

.setting-label {
  font-size: 14px;
  font-weight: 500;
  color: #333333;
  margin-bottom: 4px;
}

.setting-description {
  font-size: 12px;
  color: #666666;
  line-height: 1.5;
}

.setting-warning {
  margin-top: 8px;
  font-size: 12px;
  color: #f59e0b;
  display: flex;
  align-items: center;
  gap: 4px;
}

.setting-control {
  margin-left: 16px;
  flex-shrink: 0;
}

.toggle-switch {
  position: relative;
  width: 44px;
  height: 24px;
  background: #d1d5db;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;

  &.active {
    background: #10b981;
  }

  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.toggle-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: #ffffff;
  border-radius: 50%;
  transition: transform 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toggle-switch.active .toggle-knob {
  transform: translateX(20px);
}

.settings-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: #9ca3af;

  .placeholder-icon {
    width: 32px;
    height: 32px;
    margin-bottom: 12px;
  }

  span {
    font-size: 14px;
  }
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;

  .settings-modal {
    transition:
      transform 0.25s ease,
      opacity 0.25s ease;
  }
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;

  .settings-modal {
    transform: scale(0.95) translateY(-20px);
    opacity: 0;
  }
}
</style>
