<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="proxy-modal-overlay" @click.self="handleClose">
        <div class="proxy-modal" @click.stop>
          <div class="modal-header">
            <h2 class="modal-title">代理设置</h2>
            <button class="close-btn" @click="handleClose" aria-label="关闭">
              <IconClose />
            </button>
          </div>

          <div class="modal-body">
            <div class="proxy-section">
              <div class="setting-item">
                <div class="setting-info">
                  <div class="setting-label">代理模式</div>
                  <div class="setting-description">开启后，可配置智能代理或普通代理</div>
                </div>
                <div class="setting-control">
                  <button
                    class="toggle-switch"
                    :class="{ active: form.enabled }"
                    @click="form.enabled = !form.enabled"
                  >
                    <span class="toggle-knob"></span>
                  </button>
                </div>
              </div>
            </div>

            <template v-if="form.enabled">
              <div class="proxy-section">
                <div class="section-title">代理类型</div>
                <div class="mode-options">
                  <label class="mode-option">
                    <input v-model="form.mode" type="radio" value="smart" />
                    <span>智能代理</span>
                  </label>
                  <label class="mode-option">
                    <input v-model="form.mode" type="radio" value="normal" />
                    <span>普通代理</span>
                  </label>
                </div>
              </div>

              <template v-if="form.mode === 'smart'">
                <div class="proxy-section">
                  <div class="section-title">智能代理模式</div>
                  <div class="mode-options">
                    <label class="mode-option">
                      <input v-model="form.smartSubMode" type="radio" value="auto" />
                      <span>自动扫描模式</span>
                    </label>
                    <label class="mode-option">
                      <input v-model="form.smartSubMode" type="radio" value="manual" />
                      <span>手动代理模式</span>
                    </label>
                  </div>
                </div>

                <div v-if="form.smartSubMode === 'auto'" class="proxy-section">
                  <div class="section-title">自动扫描</div>
                  <div class="scan-area">
                    <button class="scan-btn" :disabled="proxyStore.isScanning" @click="handleScan">
                      {{ proxyStore.isScanning ? '扫描中...' : '扫描可用代理' }}
                    </button>
                    <div v-if="form.scannedProxies.length > 0" class="scan-results">
                      <div class="scan-result-label">已扫描到的代理（最多使用 5 个）：</div>
                      <div
                        v-for="(proxy, idx) in form.scannedProxies"
                        :key="idx"
                        class="scan-result-item"
                      >
                        {{ proxy }}
                      </div>
                    </div>
                  </div>
                </div>

                <div v-else class="proxy-section">
                  <div class="section-title">手动代理</div>
                  <div class="input-row">
                    <div class="input-group">
                      <label>IP 地址</label>
                      <input v-model="form.manualProxyHost" type="text" placeholder="127.0.0.1" />
                    </div>
                    <div class="input-group">
                      <label>端口</label>
                      <input
                        v-model.number="form.manualProxyPort"
                        type="number"
                        placeholder="7890"
                        min="1"
                        max="65535"
                      />
                    </div>
                  </div>
                </div>
              </template>

              <div v-else class="proxy-section">
                <div class="section-title">普通代理地址</div>
                <div class="input-group full-width">
                  <label>代理 URL（支持 http://、https://、socks5://）</label>
                  <input
                    v-model="form.normalProxyUrl"
                    type="text"
                    placeholder="http://127.0.0.1:7890"
                  />
                </div>
              </div>
            </template>
          </div>

          <div class="modal-footer">
            <button class="btn btn-secondary" @click="handleClose">取消</button>
            <button class="btn btn-primary" :disabled="proxyStore.isLoading" @click="handleSave">
              {{ proxyStore.isLoading ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useProxyStore } from '@/stores'
import type { ProxySettings } from '@/types'
import { IconClose } from '@/components/icons'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const proxyStore = useProxyStore()

const form = ref<ProxySettings>({
  enabled: false,
  mode: 'smart',
  smartSubMode: 'auto',
  manualProxyHost: '',
  manualProxyPort: 7890,
  scannedProxies: [],
  normalProxyUrl: '',
})

// 仅在弹窗打开时从 store 加载，避免 scan 等操作更新 store 时覆盖用户未保存的编辑
watch(
  () => props.visible,
  async visible => {
    if (visible) {
      await proxyStore.loadProxySettings()
      form.value = { ...proxyStore.proxySettings }
    }
  }
)

async function handleSave() {
  try {
    await proxyStore.saveProxySettings(form.value)
    emit('close')
  } catch {
    // Error handled by store / global handler
  }
}

async function handleScan() {
  try {
    const proxies = await proxyStore.scanProxyPorts()
    form.value = { ...form.value, scannedProxies: proxies }
  } catch {
    // Error handled by store
  }
}

function handleClose() {
  emit('close')
}
</script>

<style lang="scss" scoped>
.proxy-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2100;
}

.proxy-modal {
  background: #ffffff;
  border-radius: 12px;
  width: 480px;
  max-width: 90vw;
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
  overflow-y: auto;
  padding: 24px;
}

.proxy-section {
  margin-bottom: 24px;

  &:last-child {
    margin-bottom: 0;
  }
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #333333;
  margin-bottom: 12px;
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

  &:disabled {
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

.mode-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mode-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #333333;

  input {
    width: 16px;
    height: 16px;
  }
}

.scan-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scan-btn {
  padding: 8px 16px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  align-self: flex-start;

  &:hover:not(:disabled) {
    background: #e5e7eb;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.scan-results {
  padding: 12px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.scan-result-label {
  font-size: 12px;
  color: #666666;
  margin-bottom: 8px;
}

.scan-result-item {
  font-size: 13px;
  font-family: monospace;
  padding: 4px 0;
  color: #333333;
}

.input-row {
  display: flex;
  gap: 16px;
}

.input-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;

  &.full-width {
    flex: none;
    width: 100%;
  }

  label {
    font-size: 12px;
    font-weight: 500;
    color: #666666;
  }

  input {
    padding: 8px 12px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    font-size: 14px;

    &:focus {
      outline: none;
      border-color: #3b82f6;
    }
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}

.btn {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.btn-secondary {
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  color: #333333;

  &:hover:not(:disabled) {
    background: #e5e7eb;
  }
}

.btn-primary {
  background: #3b82f6;
  border: none;
  color: #ffffff;

  &:hover:not(:disabled) {
    background: #2563eb;
  }
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;

  .proxy-modal {
    transition:
      transform 0.25s ease,
      opacity 0.25s ease;
  }
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;

  .proxy-modal {
    transform: scale(0.95) translateY(-20px);
    opacity: 0;
  }
}
</style>
