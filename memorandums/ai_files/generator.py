import os
from django.conf import settings

from .vectordb import VectorStore
from .embedding import add_property_details, process_document
from .extractors import DocumentExtractor
from .chunk_store import (
    chunks_exist_for_document,
    save_chunks_for_document,
    load_chunks_into_store,
)


def _get_store_paths(memorandum_id) -> tuple:
    base_dir = os.path.join(
        settings.MEDIA_ROOT, "memorandums", "vector_stores", str(memorandum_id)
    )
    os.makedirs(base_dir, exist_ok=True)
    return (
        os.path.join(base_dir, "vector.index"),
        os.path.join(base_dir, "metadata.pkl"),
    )


def generate_memorandum(memorandum_id, property_data: dict, document_paths: list) -> dict:
    """
    Main entry point called by the Celery task.

    Flow per document:
      - If DB chunks exist  → load from DB into vector store (fast, no re-embedding)
      - If no DB chunks yet → extract from file, embed, add to vector store,
                              then save chunks+embeddings to DB for future runs
    """
    from properties.models import PropertyDocument

    index_path, meta_path = _get_store_paths(memorandum_id)

    vector_store = VectorStore(dim=384, index_path=index_path, meta_path=meta_path)
    vector_store.clear()

    # Step 1 — Add structured property details (always re-embedded; lightweight)
    add_property_details(property_data, vector_store)

    # Step 2 — Process each document: load from DB or extract fresh
    for file_path in document_paths:
        # Resolve the PropertyDocument by file path to get its DB id
        doc = PropertyDocument.objects.filter(file=_relative_path(file_path)).first()

        if doc and chunks_exist_for_document(doc.id):
            # Reuse saved chunks — skip file reading & embedding entirely
            load_chunks_into_store(doc.id, vector_store)
        else:
            # First time — extract, embed, add to store, then persist
            if os.path.isfile(file_path):
                count, chunks, embeddings = process_document(file_path, vector_store)
                if doc and count > 0:
                    save_chunks_for_document(doc.id, chunks, embeddings)

    # Step 3 — Extract all 14 sections via OpenAI
    extractor = DocumentExtractor(vector_store)
    results = extractor.extract_all()

    # Step 4 — Cleanup temporary vector store files
    vector_store.cleanup()

    return results


def _relative_path(absolute_path: str) -> str:
    """
    Convert an absolute file path back to a path relative to MEDIA_ROOT,
    which is how Django stores it in the FileField.
    """
    media_root = str(settings.MEDIA_ROOT)
    if absolute_path.startswith(media_root):
        rel = absolute_path[len(media_root):]
        return rel.lstrip(os.sep)
    return absolute_path