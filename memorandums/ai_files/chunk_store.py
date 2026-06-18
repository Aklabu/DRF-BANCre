"""
Handles saving extracted chunks+embeddings to the DB and
loading them back into a VectorStore for re-use.
"""
from properties.models import PropertyDocument, PropertyDocumentChunk


def chunks_exist_for_document(doc_id: int) -> bool:
    """Return True if chunks are already stored for this document."""
    return PropertyDocumentChunk.objects.filter(document_id=doc_id).exists()


def save_chunks_for_document(doc_id: int, chunks: list[str], embeddings: list[list[float]]) -> None:
    """
    Bulk-save text chunks and their embeddings for a PropertyDocument.
    Clears any existing chunks first to avoid duplicates on re-runs.
    """
    PropertyDocumentChunk.objects.filter(document_id=doc_id).delete()

    objs = [
        PropertyDocumentChunk(
            document_id=doc_id,
            chunk_text=chunk,
            embedding=emb,
            chunk_index=i,
        )
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ]
    PropertyDocumentChunk.objects.bulk_create(objs)


def load_chunks_into_store(doc_id: int, vector_store) -> int:
    """
    Load saved chunks from DB and add them into the provided VectorStore.
    Returns the number of chunks loaded.
    """
    qs = PropertyDocumentChunk.objects.filter(document_id=doc_id).order_by('chunk_index')
    if not qs.exists():
        return 0

    embeddings = [row.embedding for row in qs]
    texts      = [row.chunk_text for row in qs]

    vector_store.add(embeddings, texts)
    return len(texts)


def load_property_chunks_into_store(property_id: int, vector_store) -> int:
    """
    Convenience: load chunks for ALL documents of a property into the store.
    Returns total chunks loaded.
    """
    total = 0
    doc_ids = PropertyDocument.objects.filter(
        property_id=property_id
    ).values_list('id', flat=True)

    for doc_id in doc_ids:
        total += load_chunks_into_store(doc_id, vector_store)
    return total