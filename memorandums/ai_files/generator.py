import os
import uuid
from django.conf import settings

from .vectordb import VectorStore
from .embedding import add_property_details, process_document
from .extractors import DocumentExtractor


def _get_store_paths(memorandum_id) -> tuple:
    """
    Return isolated index and metadata file paths for a given memorandum ID.
    Stored under MEDIA_ROOT/memorandums/vector_stores/ so they are
    outside the Django app directory and are easily cleaned up.
    """
    base_dir = os.path.join(settings.MEDIA_ROOT, "memorandums", "vector_stores", str(memorandum_id))
    os.makedirs(base_dir, exist_ok=True)
    return (
        os.path.join(base_dir, "vector.index"),
        os.path.join(base_dir, "metadata.pkl"),
    )


def generate_memorandum(memorandum_id, property_data: dict, document_paths: list) -> dict:
    """
    Main entry point called by the Django Celery task.

    Args:
        memorandum_id:   The Memorandum model instance ID (used to isolate the vector store).
        property_data:   A dict of property fields (from the Property model).
        document_paths:  A list of absolute file paths for PropertyDocument files.

    Returns:
        A dict with 14 keys (one per section_key) mapping to AI-generated text strings.
        Example:
        {
            "property_information": "...",
            "executive_summary": "...",
            ...
            "disclaimer": "...",
        }

    Raises:
        Exception: Any error during embedding or OpenAI calls is allowed to propagate
                   so the Celery task can catch it and set status='Failed'.
    """
    index_path, meta_path = _get_store_paths(memorandum_id)

    # Always start with a clean store for this memorandum
    vector_store = VectorStore(dim=384, index_path=index_path, meta_path=meta_path)
    vector_store.clear()

    # Step 1 — Add structured property details
    add_property_details(property_data, vector_store)

    # Step 2 — Process each document file
    for file_path in document_paths:
        if os.path.isfile(file_path):
            process_document(file_path, vector_store)

    # Step 3 — Extract all 14 sections
    extractor = DocumentExtractor(vector_store)
    results = extractor.extract_all()

    # Step 4 — Cleanup temporary vector store files from disk
    vector_store.cleanup()

    return results