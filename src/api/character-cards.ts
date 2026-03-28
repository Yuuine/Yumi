import type { CharacterCardFlat } from '@/types/character'
import { httpClient } from './http-client'
import { toCharacterCardListDTO, characterCardToBackend } from '@/utils/field-mapper'

export const characterCardsApi = {
  async list(userId: string): Promise<CharacterCardFlat[]> {
    const response = await httpClient.get<Record<string, unknown>[]>('/character-cards', {
      params: { userId },
    })
    return toCharacterCardListDTO(response) as CharacterCardFlat[]
  },

  async upsert(
    userId: string,
    cardId: string,
    body: CharacterCardFlat
  ): Promise<{ success: boolean }> {
    return httpClient.put<{ success: boolean }>(
      `/character-cards/${encodeURIComponent(cardId)}`,
      characterCardToBackend(body),
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
      { cards: cards.map(card => characterCardToBackend(card)) },
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
