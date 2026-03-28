export interface DeviceFingerprint {
  fingerprint: string
  components: FingerprintComponent[]
  version: string
}

export interface FingerprintComponent {
  key: string
  value: string
  weight: number
}

const FINGERPRINT_VERSION = '2.0'

const FINGERPRINT_COMPONENTS = [
  'language',
  'platform',
  'screenWidth',
  'screenHeight',
  'colorDepth',
  'timezone',
] as const

export async function generateDeviceFingerprint(): Promise<DeviceFingerprint> {
  const components: FingerprintComponent[] = []

  for (const key of FINGERPRINT_COMPONENTS) {
    let value: string

    switch (key) {
      case 'language':
        value = navigator.language
        break
      case 'platform':
        value = navigator.platform
        break
      case 'screenWidth':
        value = screen.width.toString()
        break
      case 'screenHeight':
        value = screen.height.toString()
        break
      case 'colorDepth':
        value = screen.colorDepth.toString()
        break
      case 'timezone':
        value = Intl.DateTimeFormat().resolvedOptions().timeZone
        break
      default:
        value = ''
    }

    components.push({ key, value, weight: 1 })
  }

  const combined = components.map(c => c.value).join('|')
  const encoder = new TextEncoder()
  const data = encoder.encode(combined)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const fingerprint = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')

  return { fingerprint, components, version: FINGERPRINT_VERSION }
}
