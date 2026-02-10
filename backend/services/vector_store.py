"""
FAISS-based vector store for semantic search in SuccessStore.
Enables RAG-based retrieval of similar past diagnostic cases.
"""
from typing import List, Dict, Optional, Tuple
import json
from pathlib import Path
import numpy as np

from backend.config import settings
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)

# Lazy imports for optional dependencies
_faiss = None
_sentence_transformers = None


def _get_faiss():
    """Lazy import of FAISS."""
    global _faiss
    if _faiss is None:
        try:
            import faiss
            _faiss = faiss
            logger.info("FAISS loaded successfully")
        except ImportError:
            logger.warning("FAISS not installed. Vector search disabled.")
            logger.warning("Install with: pip install faiss-cpu")
    return _faiss


def _get_embedder():
    """Lazy import of SentenceTransformers."""
    global _sentence_transformers
    if _sentence_transformers is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_transformers = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("SentenceTransformer loaded: all-MiniLM-L6-v2")
        except ImportError:
            logger.warning("sentence-transformers not installed. Using fallback embeddings.")
            logger.warning("Install with: pip install sentence-transformers")
    return _sentence_transformers


class SimpleEmbedder:
    """Fallback embedder when sentence-transformers not available."""
    
    def __init__(self, dim: int = 384):
        self.dim = dim
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """Generate simple hash-based embeddings."""
        embeddings = []
        for text in texts:
            # Simple deterministic embedding from text hash
            np.random.seed(hash(text) % (2**32))
            emb = np.random.randn(self.dim).astype(np.float32)
            emb /= np.linalg.norm(emb)  # Normalize
            embeddings.append(emb)
        return np.array(embeddings)


class VectorStore:
    """
    FAISS-based vector store for semantic case retrieval.
    Falls back to brute-force search if FAISS not available.
    """
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = None
        self.documents: List[Dict] = []
        self.embeddings: Optional[np.ndarray] = None
        
        # Try to use FAISS
        faiss = _get_faiss()
        if faiss is not None:
            self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine after normalization)
            logger.info(f"FAISS index created: dim={dimension}")
        else:
            logger.info("Using numpy fallback for vector search")
        
        # Get embedder
        self.embedder = _get_embedder() or SimpleEmbedder(dimension)
    
    def add_case(
        self,
        case_id: str,
        symptoms: List[str],
        diagnosis: str,
        confidence: float,
        metadata: Optional[Dict] = None
    ):
        """
        Add a diagnostic case to the vector store.
        
        Args:
            case_id: Unique case identifier
            symptoms: List of symptoms
            diagnosis: Final diagnosis
            confidence: Diagnosis confidence (0-1)
            metadata: Additional case metadata
        """
        # Create text representation for embedding
        text = f"Symptoms: {', '.join(symptoms)}. Diagnosis: {diagnosis}"
        
        # Generate embedding
        embedding = self.embedder.encode([text])[0].astype(np.float32)
        embedding /= np.linalg.norm(embedding)  # Normalize for cosine similarity
        
        # Store document
        doc = {
            "case_id": case_id,
            "symptoms": symptoms,
            "diagnosis": diagnosis,
            "confidence": confidence,
            "metadata": metadata or {}
        }
        self.documents.append(doc)
        
        # Add to index
        if self.index is not None:
            self.index.add(embedding.reshape(1, -1))
        else:
            # Numpy fallback
            if self.embeddings is None:
                self.embeddings = embedding.reshape(1, -1)
            else:
                self.embeddings = np.vstack([self.embeddings, embedding])
        
        logger.debug(f"Added case {case_id} to vector store")
    
    def search(
        self,
        query_symptoms: List[str],
        top_k: int = 5
    ) -> List[Tuple[Dict, float]]:
        """
        Search for similar cases by symptoms.
        
        Args:
            query_symptoms: List of symptoms to search for
            top_k: Number of results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if not self.documents:
            return []
        
        # Create query embedding
        query_text = f"Symptoms: {', '.join(query_symptoms)}"
        query_embedding = self.embedder.encode([query_text])[0].astype(np.float32)
        query_embedding /= np.linalg.norm(query_embedding)
        
        # Search
        if self.index is not None:
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1),
                min(top_k, len(self.documents))
            )
            results = [
                (self.documents[idx], float(dist))
                for idx, dist in zip(indices[0], distances[0])
                if idx < len(self.documents)
            ]
        else:
            # Numpy fallback
            if self.embeddings is None:
                return []
            similarities = np.dot(self.embeddings, query_embedding)
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            results = [
                (self.documents[idx], float(similarities[idx]))
                for idx in top_indices
            ]
        
        logger.info(f"Found {len(results)} similar cases for query")
        return results
    
    def save(self, path: Path):
        """Save vector store to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save documents
        with open(path / "documents.json", "w") as f:
            json.dump(self.documents, f, indent=2)
        
        # Save embeddings
        if self.index is not None:
            faiss = _get_faiss()
            if faiss:
                faiss.write_index(self.index, str(path / "faiss.index"))
        elif self.embeddings is not None:
            np.save(path / "embeddings.npy", self.embeddings)
        
        logger.info(f"Vector store saved: {len(self.documents)} documents")
    
    def load(self, path: Path) -> bool:
        """Load vector store from disk."""
        path = Path(path)
        
        # Load documents
        docs_path = path / "documents.json"
        if not docs_path.exists():
            return False
        
        with open(docs_path) as f:
            self.documents = json.load(f)
        
        # Load embeddings
        faiss_path = path / "faiss.index"
        numpy_path = path / "embeddings.npy"
        
        faiss = _get_faiss()
        if faiss_path.exists() and faiss:
            self.index = faiss.read_index(str(faiss_path))
        elif numpy_path.exists():
            self.embeddings = np.load(numpy_path)
        
        logger.info(f"Vector store loaded: {len(self.documents)} documents")
        return True
    
    def __len__(self) -> int:
        return len(self.documents)


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create VectorStore instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        
        # Try to load from disk
        store_path = settings.data_dir / "vector_store"
        if store_path.exists():
            _vector_store.load(store_path)
    
    return _vector_store
