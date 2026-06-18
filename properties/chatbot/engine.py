import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

SYSTEM_PROMPT = (
    "You are a real estate assistant. Answer questions strictly based on "
    "the provided context extracted from the property's documents. "
    "If the answer is not in the context, say so clearly. Be concise and factual."
)


def _get_client() -> OpenAI:
    try:
        from django.conf import settings
        api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
    except Exception:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")
    return OpenAI(api_key=api_key)


def _retrieve(property_id: int, query: str, top_k: int = 6) -> list[str]:
    from properties.models import PropertyDocumentChunk

    qs = PropertyDocumentChunk.objects.filter(
        document__property_id=property_id
    ).order_by('document', 'chunk_index')

    if not qs.exists():
        return []

    chunks     = [row.chunk_text for row in qs]
    embeddings = np.array([row.embedding for row in qs], dtype='float32')

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    query_vec = embed_model.encode([query])[0].astype('float32').reshape(1, -1)
    _, indices = index.search(query_vec, min(top_k, index.ntotal))

    return [chunks[i] for i in indices[0] if i < len(chunks)]


def ask(property_id: int, message: str, history: list[dict] = None) -> str:
    context = _retrieve(property_id, message)

    if not context:
        return "No document data is available for this property yet."

    context_text = "\n\n".join(context)

    client   = _get_client()
    messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nContext:\n{context_text}"}
    ]

    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()