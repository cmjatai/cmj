"""
Integração com a API Gemini. Specs em docs/specs/genia/.

- base: IAGenaiBase, conexão e controle de cota (sem regra de funcionalidade)
- chat: IAChatService, chat RAG
- embeddings: IAEmbeddingService, vetorização para a busca semântica
- classificacao: IAClassificacaoMateriaService
- similaridade: IAAnaliseSimilaridadeService
- loa_agrupamento: IAEmentaEmendaColetiva

Os três últimos não são importados aqui porque dependem de models de outros apps.
"""

from cmj.utils.genia.base import IAGenaiBase, IAQuotaUnavailableError
from cmj.utils.genia.chat import IAChatService
from cmj.utils.genia.embeddings import IAEmbeddingService

__all__ = [
    "IAChatService",
    "IAEmbeddingService",
    "IAGenaiBase",
    "IAQuotaUnavailableError",
]
