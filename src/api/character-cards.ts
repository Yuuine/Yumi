import type { CharacterCardFlat } from '@/types/character'
import { httpClient } from './http-client'
import { toCharacterCardListDTO, characterCardToBackend } from '@/utils/field-mapper'
import { apiCache } from '@/utils/api-cache'

export const characterCardsApi = {
  async list(userId: string): Promise<CharacterCardFlat[]> {
    const response = await httpClient.get<Record<string, unknown>[]>('/character-cards', {
      params: { userId },
      cache: true,
      ttl: 120000,
    })
    return toCharacterCardListDTO(response) as CharacterCardFlat[]
  },

  async upsert(
    userId: string,
    cardId: string,
    body: CharacterCardFlat
  ): Promise<{ success: boolean }> {
    const result = await httpClient.put<{ success: boolean }>(
      `/character-cards/${encodeURIComponent(cardId)}`,
      characterCardToBackend(body),
      {
        params: { userId },
      }
    )
    apiCache.invalidatePattern('GET:/character-cards')
    return result
  },

  async batchUpsert(
    userId: string,
    cards: (CharacterCardFlat & { id: string })[]
  ): Promise<{ success: boolean; count: number }> {
    const result = await httpClient.put<{ success: boolean; count: number }>(
      '/character-cards/batch',
      { cards: cards.map(card => characterCardToBackend(card)) },
      { params: { userId } }
    )
    apiCache.invalidatePattern('GET:/character-cards')
    return result
  },

  async remove(userId: string, cardId: string): Promise<{ success: boolean }> {
    const result = await httpClient.delete<{ success: boolean }>(
      `/character-cards/${encodeURIComponent(cardId)}`,
      {
        params: { userId },
      }
    )
    apiCache.invalidatePattern('GET:/character-cards')
    return result
  },
}
