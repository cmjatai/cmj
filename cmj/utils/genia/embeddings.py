import logging
import time

from google.genai import types

from cmj.utils.genia.base import IAGenaiBase

logger = logging.getLogger(__name__)


class IAEmbeddingService(IAGenaiBase):
    """
    Vetorização de documentos e de consultas para a busca semântica.

    Não consome IAQuota. Spec: docs/specs/genia/embeddings.md
    """

    quota_exempt = True

    EMBED_MODEL = "gemini-embedding-2"
    EMBED_DIMENSIONS = 1536
    EMBED_MAX_ATTEMPTS = 3
    EMBED_RETRY_BASE_DELAY = 2  # segundos; dobra a cada tentativa
    EMBED_MAX_CONSECUTIVE_FAILED_BATCHES = 2

    def prepare_document(self, text: str, title: str | None = None) -> str:
        """Formata o texto de acordo com o padrão exigido pelo modelo."""
        doc_title = title.strip() if title else "none"
        return f"title: {doc_title} | text: {text}"

    def prepare_query(self, query: str, is_qa_mode: bool = True) -> str:
        """Prepara uma query de recuperação de acordo com o padrão exigido pelo modelo."""
        task_prefix = "question answering" if is_qa_mode else "search result"
        return f"task: {task_prefix} | query: {query}"

    def get_query_embedding(
        self,
        query_text: str,
        model: str = EMBED_MODEL,
        is_qa_mode: bool = True,
    ):
        response = self.client.models.embed_content(
            model=model,
            contents=[self.prepare_query(query_text, is_qa_mode=is_qa_mode)],
            config=types.EmbedContentConfig(
                output_dimensionality=self.EMBED_DIMENSIONS,
            ),
        )
        return response.embeddings[0].values

    def _embed_texts(self, texts, model, attempts):
        last_error = None
        for attempt in range(attempts):
            try:
                response = self.client.models.embed_content(
                    model=model,
                    contents=texts,
                    config=types.EmbedContentConfig(
                        output_dimensionality=self.EMBED_DIMENSIONS,
                        # task_type NÃO é incluído aqui
                    ),
                )
                vectors = [emb.values for emb in response.embeddings]
                if len(vectors) != len(texts):
                    raise ValueError(
                        f"API retornou {len(vectors)} vetores para {len(texts)} textos."
                    )
                return vectors
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Falha ao gerar embeddings (tentativa {attempt + 1}): {e}"
                )
                if attempt < attempts - 1:
                    time.sleep(self.EMBED_RETRY_BASE_DELAY * 2**attempt)
        raise last_error

    def embed_documents(
        self,
        documents: list[dict],  # [{'text': '...', 'title': '...'}, ...]
        model: str = EMBED_MODEL,
        batch_size: int = 64,
    ):
        """
        Retorna uma lista alinhada a `documents`; documentos que falharam
        ficam como None. Se vários lotes seguidos falharem por completo
        (API fora do ar/cota), interrompe e devolve a lista parcial.
        """
        all_embeddings = []
        failed_batches = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]

            # Aplica a formatação oficial do modelo novo em cada documento
            formatted_batch = [
                self.prepare_document(doc["text"], doc.get("title")) for doc in batch
            ]

            try:
                vectors = self._embed_texts(
                    formatted_batch, model, self.EMBED_MAX_ATTEMPTS
                )
            except Exception as e:
                # Isola o documento problemático (ex.: texto acima do limite do
                # modelo) para que não derrube os demais do lote.
                logger.error(
                    f"Erro no lote de embeddings, reprocessando individualmente: {e}"
                )
                vectors = []
                for text in formatted_batch:
                    try:
                        vectors.extend(self._embed_texts([text], model, attempts=1))
                    except Exception as single_error:
                        logger.error(f"Documento sem embedding: {single_error}")
                        vectors.append(None)

            all_embeddings.extend(vectors)

            if any(vectors):
                failed_batches = 0
            else:
                failed_batches += 1
                if failed_batches >= self.EMBED_MAX_CONSECUTIVE_FAILED_BATCHES:
                    logger.error(
                        "Geração de embeddings interrompida: lotes seguidos falharam."
                    )
                    break

        return all_embeddings
