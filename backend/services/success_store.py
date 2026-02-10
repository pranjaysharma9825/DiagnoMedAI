"""
Success Store - RAG-based storage for successful diagnostic outcomes.
Stores completed diagnoses for retrieval-augmented generation.
"""
from typing import List, Optional, Dict
from datetime import datetime
import json
from pathlib import Path

from backend.models.diagnosis import DiagnosisResult
from backend.config import settings
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class SuccessStore:
    """
    Stores successful diagnostic outcomes for RAG retrieval.
    Uses JSON file storage for MVP (upgradeable to vector DB).
    """
    
    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = store_path or (settings.data_dir / "success_store.json")
        self.entries: List[Dict] = []
        self._load()
        logger.info(f"SuccessStore initialized with {len(self.entries)} entries")
    
    def _load(self):
        """Load existing entries from disk."""
        if self.store_path.exists():
            try:
                with open(self.store_path, 'r') as f:
                    self.entries = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load success store: {e}")
                self.entries = []
    
    def _save(self):
        """Persist entries to disk."""
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.store_path, 'w') as f:
                json.dump(self.entries, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save success store: {e}")
    
    def add_success(self, result: DiagnosisResult, feedback_score: int = 5) -> str:
        """
        Add a successful diagnosis to the store.
        
        Args:
            result: The diagnosis result
            feedback_score: User feedback 1-5
            
        Returns:
            Entry ID
        """
        entry_id = f"success_{len(self.entries) + 1:04d}"
        
        entry = {
            "id": entry_id,
            "patient_id": result.patient_id,
            "diagnosis": result.final_diagnosis.name,
            "disease_id": result.final_diagnosis.disease_id,
            "confidence": result.confidence,
            "tests_used": result.tests_ordered,
            "total_cost": result.total_cost,
            "iterations": result.iterations,
            "feedback_score": feedback_score,
            "timestamp": datetime.now().isoformat()
        }
        
        self.entries.append(entry)
        self._save()
        logger.info(f"Added success entry {entry_id}: {result.final_diagnosis.name}")
        
        return entry_id
    
    def find_similar(
        self,
        disease_id: Optional[str] = None,
        symptoms: Optional[List[str]] = None,
        limit: int = 5,
        use_vector_search: bool = True
    ) -> List[Dict]:
        """
        Find similar past diagnoses for RAG.
        
        Args:
            disease_id: Filter by disease
            symptoms: Symptoms for semantic search
            limit: Max results
            use_vector_search: Use FAISS for semantic similarity
            
        Returns:
            List of similar success entries
        """
        # Try vector search if symptoms provided
        if symptoms and use_vector_search:
            try:
                from backend.services.vector_store import get_vector_store
                vs = get_vector_store()
                if len(vs) > 0:
                    similar = vs.search(symptoms, top_k=limit)
                    results = []
                    for doc, score in similar:
                        # Merge with entry data
                        entry = next(
                            (e for e in self.entries if e.get('id') == doc.get('case_id')),
                            doc
                        )
                        entry['similarity_score'] = score
                        results.append(entry)
                    return results
            except Exception as e:
                logger.debug(f"Vector search fallback: {e}")
        
        # Fallback to keyword matching
        results = self.entries.copy()
        
        if disease_id:
            results = [e for e in results if e.get('disease_id') == disease_id]
        
        # Sort by recency and feedback
        results.sort(
            key=lambda x: (x.get('feedback_score', 3), x.get('timestamp', '')),
            reverse=True
        )
        
        return results[:limit]
    
    def get_stats(self) -> Dict:
        """Get store statistics."""
        if not self.entries:
            return {"total": 0}
        
        avg_confidence = sum(e.get('confidence', 0) for e in self.entries) / len(self.entries)
        avg_cost = sum(e.get('total_cost', 0) for e in self.entries) / len(self.entries)
        avg_iterations = sum(e.get('iterations', 0) for e in self.entries) / len(self.entries)
        
        return {
            "total": len(self.entries),
            "avg_confidence": round(avg_confidence, 3),
            "avg_cost": round(avg_cost, 2),
            "avg_iterations": round(avg_iterations, 1)
        }


# Singleton
_store_instance: Optional[SuccessStore] = None


def get_success_store() -> SuccessStore:
    """Get or create the success store."""
    global _store_instance
    if _store_instance is None:
        _store_instance = SuccessStore()
    return _store_instance
