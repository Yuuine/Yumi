import type { CharacterCardFlat } from '@/types/character'
import { httpClient } from './http-client'

export const characterCardsApi = {
  async list(userId: string): Promise<CharacterCardFlat[]> {
    return httpClient.get<CharacterCardFlat[]>('/character-cards', {
      params: { userId },
    })
  },

  async upsert(
    userId: string,
    cardId: string,
    body: CharacterCardFlat
  ): Promise<{ success: boolean }> {
    return httpClient.put<{ success: boolean }>(
      `/character-cards/${encodeURIComponent(cardId)}`,
      body,
      {
        params: { userId },
      }
    )
  },

  async batchUpsert(
    userId: string,
    cards: (CharacterCardFlat & { id: string })[]
  ): Promise<{ success: boolean; count: number }> {
    return httpClient.put<{ success: boolean; count: number }>(
      '/character-cards/batch',
      { cards },
      { params: { userId } }
    )
  },

  async remove(userId: string, cardId: string): Promise<{ success: boolean }> {
    return httpClient.delete<{ success: boolean }>(
      `/character-cards/${encodeURIComponent(cardId)}`,
      {
        params: { userId },
      }
    )
  },
}
