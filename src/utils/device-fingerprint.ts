export interface DeviceFingerprint {
  fingerprint: string
  components: FingerprintComponent[]
}

export interface FingerprintComponent {
  key: string
  value: string
  weight: number
}

const FINGERPRINT_COMPONENTS = [
  'userAgent',
  'language',
  'platform',
  'screenWidth',
  'screenHeight',
  'colorDepth',
  'timezone',
  'canvasFingerprint',
  'webglFingerprint',
] as const

function getCanvasFingerprint(): string {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  if (!ctx) return 'no-canvas'

  canvas.width = 200
  canvas.height = 50

  ctx.textBaseline = 'alphabetic'
  ctx.font = "14px 'Arial'"
  ctx.fillStyle = '#f60'
  ctx.fillRect(125, 1, 62, 20)
  ctx.fillStyle = '#069'
  ctx.fillText('Yumi Device FP', 2, 15)
  ctx.fillStyle = 'rgba(102, 204, 0, 0.7)'
  ctx.fillText('Yumi Device FP', 4, 17)

  return canvas.toDataURL().slice(-50)
}

function getWebGLFingerprint(): string {
  const canvas = document.createElement('canvas')
  const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
  if (!gl) return 'no-webgl'

  const debugInfo = (gl as WebGLRenderingContext).getExtension('WEBGL_debug_renderer_info')
  if (!debugInfo) return 'no-debug-info'

  const renderer = (gl as WebGLRenderingContext).getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
  const vendor = (gl as WebGLRenderingContext).getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)

  return `${vendor}~${renderer}`.slice(-100)
}

export async function generateDeviceFingerprint(): Promise<DeviceFingerprint> {
  const components: FingerprintComponent[] = []

  for (const key of FINGERPRINT_COMPONENTS) {
    let value: string

    switch (key) {
      case 'userAgent':
        value = navigator.userAgent
        break
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
      case 'canvasFingerprint':
        value = getCanvasFingerprint()
        break
      case 'webglFingerprint':
        value = getWebGLFingerprint()
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

  return { fingerprint, components }
}
