export interface Avatar {
  id: string
  path: string
  name: string
}

export const DEFAULT_AVATAR_PATH = '/avatars/default-avatar.svg'

export const AVATARS: Avatar[] = [
  { id: 'avatar1', path: '/avatars/avatars1.png', name: '头像1' },
  { id: 'avatar2', path: '/avatars/avatars2.png', name: '头像2' },
  { id: 'avatar3', path: '/avatars/avatars3.png', name: '头像3' },
  { id: 'avatar4', path: '/avatars/avatars4.png', name: '头像4' },
  { id: 'avatar5', path: '/avatars/avatars5.png', name: '头像5' },
]

export function getRandomAvatar(): string {
  const randomIndex = Math.floor(Math.random() * AVATARS.length)
  return AVATARS[randomIndex].id
}

export function getAvatarById(id: string): Avatar | undefined {
  return AVATARS.find(avatar => avatar.id === id)
}

export function getAvatarPath(id: string): string {
  const avatar = getAvatarById(id)
  return avatar?.path || DEFAULT_AVATAR_PATH
}
