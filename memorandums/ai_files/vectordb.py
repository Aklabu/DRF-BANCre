import faiss
import numpy as np
import os
import pickle


class VectorStore:
    def __init__(self, dim: int, index_path: str, meta_path: str):
        """
        Initialize VectorStore with explicit paths.
        Paths must be provided by the caller (e.g. keyed by memorandum ID)
        so that concurrent generations never collide.
        """
        self.dim = dim
        self.index_path = index_path
        self.meta_path = meta_path
        self.index = faiss.IndexFlatL2(dim)
        self._metadata = {}

        if os.path.exists(index_path) and os.path.exists(meta_path):
            self.load()

    def add(self, vectors: list, texts: list):
        np_vectors = np.array(vectors).astype("float32")
        start_idx = self.index.ntotal

        self.index.add(np_vectors)
        for i, text in enumerate(texts):
            self._metadata[start_idx + i] = text

        self.save()

    def search(self, query_vector: list, top_k: int = 3) -> list:
        query = np.array([query_vector]).astype("float32")
        distances, indices = self.index.search(query, top_k)
        return [self._metadata[i] for i in indices[0] if i in self._metadata]

    def batch_search(self, query_vectors: list, top_k: int = 3) -> list:
        """Search multiple queries in a single FAISS call."""
        queries = np.array(query_vectors).astype("float32")
        distances, indices = self.index.search(queries, top_k)

        results = []
        for query_indices in indices:
            results.append([self._metadata[i] for i in query_indices if i in self._metadata])
        return results

    def clear(self):
        self.index = faiss.IndexFlatL2(self.dim)
        self._metadata = {}
        self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self._metadata, f)

    def load(self):
        self.index = faiss.read_index(self.index_path)
        with open(self.meta_path, "rb") as f:
            data = pickle.load(f)
            # Handle both old list format and new dict format
            if isinstance(data, list):
                self._metadata = {i: text for i, text in enumerate(data)}
            else:
                self._metadata = data

    def cleanup(self):
        """Delete index files from disk after generation is complete."""
        for path in (self.index_path, self.meta_path):
            if os.path.exists(path):
                os.remove(path)
