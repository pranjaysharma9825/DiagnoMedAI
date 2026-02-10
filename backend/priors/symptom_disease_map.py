"""
Symptom-disease mapping for generating disease candidates from symptoms.
CSV-based approach for MVP, upgradeable to Neo4j graph database.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from backend.config import settings
from backend.models.diagnosis import Disease
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class SymptomDiseaseMapper:
    """
    Map patient symptoms to disease candidates with likelihood scores.
    Uses CSV-based symptom-disease associations.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.knowledge_dir
        self._load_data()
        logger.info(
            f"SymptomDiseaseMapper initialized: "
            f"{len(self.diseases)} diseases, "
            f"{len(self.symptoms)} symptoms, "
            f"{len(self.mapping)} mappings"
        )
    
    def _load_data(self):
        """Load all knowledge base CSVs."""
        # Load diseases
        diseases_path = self.data_dir / "diseases.csv"
        if diseases_path.exists():
            self.diseases = pd.read_csv(diseases_path, on_bad_lines='warn')
        else:
            logger.warning(f"Diseases file not found: {diseases_path}")
            self.diseases = pd.DataFrame()
        
        # Load symptoms
        symptoms_path = self.data_dir / "symptoms.csv"
        if symptoms_path.exists():
            self.symptoms = pd.read_csv(symptoms_path)
        else:
            logger.warning(f"Symptoms file not found: {symptoms_path}")
            self.symptoms = pd.DataFrame()
        
        # Load symptom-disease mapping
        mapping_path = self.data_dir / "symptom_disease.csv"
        if mapping_path.exists():
            self.mapping = pd.read_csv(mapping_path)
        else:
            logger.warning(f"Symptom-disease mapping not found: {mapping_path}")
            self.mapping = pd.DataFrame()
        
        # Note: tests.csv is loaded separately by DrTestChooser with custom parsing
        self.tests = pd.DataFrame()
    
    def match_symptom(self, symptom_text: str) -> Optional[str]:
        """
        Match free-text symptom to a symptom_id using name and synonyms.
        
        Args:
            symptom_text: User-provided symptom description
            
        Returns:
            symptom_id if matched, None otherwise
        """
        if self.symptoms.empty:
            return None
        
        symptom_lower = symptom_text.lower().strip()
        
        # Check exact name match
        name_match = self.symptoms[
            self.symptoms['name'].str.lower() == symptom_lower
        ]
        if not name_match.empty:
            return name_match.iloc[0]['symptom_id']
        
        # Check partial name match
        partial_match = self.symptoms[
            self.symptoms['name'].str.lower().str.contains(symptom_lower, na=False)
        ]
        if not partial_match.empty:
            return partial_match.iloc[0]['symptom_id']
        
        # Check synonyms
        if 'synonyms' in self.symptoms.columns:
            for _, row in self.symptoms.iterrows():
                synonyms = str(row.get('synonyms', '')).lower()
                if symptom_lower in synonyms:
                    return row['symptom_id']
        
        logger.debug(f"No match found for symptom: {symptom_text}")
        return None
    
    def get_disease_name(self, disease_id: str) -> Optional[str]:
        """Get disease name by ID."""
        if self.diseases.empty:
            return None
        match = self.diseases[self.diseases['disease_id'] == disease_id]
        if not match.empty:
            return match.iloc[0]['name']
        return None

    def get_candidates(
        self,
        symptoms: List[str],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get disease candidates matching the given symptoms.
        
        Args:
            symptoms: List of symptom names or IDs
            top_k: Maximum number of candidates to return
            
        Returns:
            List of disease candidates with scores
        """
        if self.mapping.empty or self.diseases.empty:
            logger.warning("Knowledge base not loaded, returning empty candidates")
            return []
        
        # Convert symptom names to IDs
        symptom_ids = []
        for symptom in symptoms:
            if symptom.startswith('S'):  # Already an ID
                symptom_ids.append(symptom)
            else:
                matched_id = self.match_symptom(symptom)
                if matched_id:
                    symptom_ids.append(matched_id)
        
        if not symptom_ids:
            logger.warning(f"No symptoms matched from: {symptoms}")
            return []
        
        logger.debug(f"Matched symptom IDs: {symptom_ids}")
        
        # Find diseases matching these symptoms
        disease_scores: Dict[str, Tuple[float, int]] = {}  # disease_id -> (total_likelihood, count)
        
        for symptom_id in symptom_ids:
            matches = self.mapping[self.mapping['symptom_id'] == symptom_id]
            
            for _, row in matches.iterrows():
                disease_id = row['disease_id']
                likelihood = float(row.get('likelihood', 0.5))
                
                if disease_id in disease_scores:
                    current_score, count = disease_scores[disease_id]
                    # Bayesian-ish combination: multiply likelihoods
                    disease_scores[disease_id] = (current_score * likelihood, count + 1)
                else:
                    disease_scores[disease_id] = (likelihood, 1)
        
        # Rank by combined score (likelihood * symptom count bonus)
        ranked = []
        for disease_id, (score, count) in disease_scores.items():
            # Boost score by number of matching symptoms
            final_score = score * (1 + 0.2 * count)
            ranked.append((disease_id, final_score, count))
        
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        # Take top candidates and normalize probabilities among them only
        top_ranked = ranked[:top_k]
        total_score = sum(score for _, score, _ in top_ranked)
        if total_score == 0:
            total_score = 1  # Avoid division by zero
        
        # Build result with disease details
        candidates = []
        for disease_id, score, matching_count in top_ranked:
            disease_info = self.get_disease(disease_id)
            if disease_info:
                # Normalize probability among top candidates only
                normalized_prob = score / total_score
                # Scale to make probabilities more meaningful (top disease should be ~40-70%)
                candidates.append({
                    "disease_id": disease_id,
                    "name": disease_info.get('name', 'Unknown'),
                    "category": disease_info.get('category', 'Unknown'),
                    "severity": disease_info.get('severity', 3),
                    "base_probability": round(normalized_prob, 3),
                    "raw_score": round(score, 4),
                    "matching_symptoms": matching_count,
                    "total_symptoms": len(symptom_ids)
                })
        
        logger.info(f"Found {len(candidates)} disease candidates for {len(symptom_ids)} symptoms")
        return candidates
    
    def get_disease(self, disease_id: str) -> Optional[Dict]:
        """Get disease information by ID."""
        if self.diseases.empty:
            return None
        
        match = self.diseases[self.diseases['disease_id'] == disease_id]
        if match.empty:
            return None
        
        row = match.iloc[0]
        return row.to_dict()
    
    def get_disease_model(self, disease_id: str) -> Optional[Disease]:
        """Get disease as a Pydantic model."""
        info = self.get_disease(disease_id)
        if not info:
            return None
        
        return Disease(
            disease_id=info['disease_id'],
            name=info['name'],
            icd10_code=info.get('icd10_code'),
            category=info.get('category'),
            severity=int(info.get('severity', 3)),
            description=info.get('description'),
            typical_duration_days=int(info.get('typical_duration_days', -1))
        )
    
    def get_symptoms_for_disease(self, disease_id: str) -> List[Dict]:
        """Get all symptoms associated with a disease."""
        if self.mapping.empty:
            return []
        
        matches = self.mapping[self.mapping['disease_id'] == disease_id]
        symptoms = []
        
        for _, row in matches.iterrows():
            symptom_id = row['symptom_id']
            symptom_info = self.symptoms[self.symptoms['symptom_id'] == symptom_id]
            
            if not symptom_info.empty:
                symptoms.append({
                    "symptom_id": symptom_id,
                    "name": symptom_info.iloc[0]['name'],
                    "likelihood": float(row.get('likelihood', 0.5)),
                    "is_pathognomonic": bool(row.get('is_pathognomonic', False)),
                    "onset_timing": row.get('onset_timing', 'unknown')
                })
        
        return symptoms


# Singleton instance  
_mapper_instance: Optional[SymptomDiseaseMapper] = None


def get_symptom_disease_mapper() -> SymptomDiseaseMapper:
    """Get or create the symptom-disease mapper instance."""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = SymptomDiseaseMapper()
    return _mapper_instance
