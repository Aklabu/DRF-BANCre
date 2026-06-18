import os
from pathlib import Path
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")


def _extract_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    try:
        if ext == ".pdf":
            return _extract_pdf(file_path)
        elif ext in (".docx", ".doc"):
            return _extract_docx(file_path)
        else:
            return ""
    except Exception:
        return ""


def _extract_pdf(file_path: str) -> str:
    import pdfplumber
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def _extract_docx(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def process_document(file_path: str, vector_store) -> tuple[int, list[str], list[list[float]]]:
    """
    Extract text from a file, chunk it, embed it, add to vector store.

    NOW ALSO returns (chunk_count, chunks, embeddings) so the caller
    can persist them to the DB via chunk_store.save_chunks_for_document().
    """
    text = _extract_text(file_path)
    if not text.strip():
        return 0, [], []

    chunks = _split_text(text)
    if not chunks:
        return 0, [], []

    embeddings = model.encode(chunks, batch_size=32)
    embeddings_list = [e.tolist() for e in embeddings]

    vector_store.add(embeddings_list, chunks)
    return len(chunks), chunks, embeddings_list      # <-- now returns data


def add_property_details(property_data: dict, vector_store) -> tuple[str, list[float]]:
    """
    Format property details, embed, add to vector store.

    NOW ALSO returns (text, embedding) so the caller can persist it.
    """
    text = f"""Property: {property_data.get('property_name', '')}
Address: {property_data.get('property_address', '')}
Type: {property_data.get('property_type', '')}
Units: {property_data.get('number_of_units', '')}
Rentable Area: {property_data.get('rentable_area', '')} SF
Year Built: {property_data.get('year_built', '')}
Year Renovated: {property_data.get('year_renovated', 'N/A')}
Occupancy: {property_data.get('occupancy', '')}%
Parking Spaces: {property_data.get('parking_spaces', '')}
Latitude: {property_data.get('latitude', '')}
Longitude: {property_data.get('longitude', '')}"""

    embedding = model.encode([text])[0].tolist()
    vector_store.add([embedding], [text])
    return text, embedding                           