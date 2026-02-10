"""
Genomic risk engine for disease risk modification based on genetic variants.
Loads risk allele data from CSV and computes risk multipliers.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

from backend.config import settings
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class GenomicRiskEngine:
    """
    Compute disease risk modifications based on patient genetic variants.
    Uses local CSV data for variant-disease associations.
    """
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or (settings.genomic_dir / "risk_alleles.csv")
        self._load_data()
        logger.info(f"GenomicRiskEngine initialized with {len(self.risk_data)} risk alleles")
    
    def _load_data(self):
        """Load risk allele data from CSV."""
        if not self.data_path.exists():
            logger.warning(f"Risk alleles file not found: {self.data_path}")
            self.risk_data = pd.DataFrame()
            return
        
        self.risk_data = pd.read_csv(self.data_path)
        logger.debug(f"Loaded {len(self.risk_data)} risk allele records")
    
    def get_risk_modifiers(
        self,
        patient_variants: List[str],
        population: str = "Global"
    ) -> Dict[str, float]:
        """
        Calculate disease risk multipliers based on patient's genetic variants.
        
        Args:
            patient_variants: List of rsIDs the patient has (e.g., ["rs1234567", "rs7903146"])
            population: Population for ancestry-specific risks
            
        Returns:
            Dictionary mapping disease_id to cumulative risk multiplier
        """
        if self.risk_data.empty or not patient_variants:
            return {}
        
        risk_modifiers: Dict[str, float] = {}
        
        for rsid in patient_variants:
            rsid = rsid.strip().lower()
            
            # Find matching risk alleles
            matches = self.risk_data[
                self.risk_data['rsid'].str.lower() == rsid
            ]
            
            # Filter by population if not Global
            if population != "Global":
                pop_matches = matches[
                    (matches['population'].str.lower() == population.lower()) |
                    (matches['population'].str.lower() == "global")
                ]
                if not pop_matches.empty:
                    matches = pop_matches
            
            for _, row in matches.iterrows():
                disease_id = row['disease_id']
                multiplier = float(row['risk_multiplier'])
                
                # Cumulative risk (multiply existing)
                if disease_id in risk_modifiers:
                    risk_modifiers[disease_id] *= multiplier
                else:
                    risk_modifiers[disease_id] = multiplier
                
                logger.debug(
                    f"Variant {rsid} -> {disease_id}: {multiplier}x "
                    f"(gene: {row.get('gene', 'unknown')})"
                )
        
        logger.info(f"Computed {len(risk_modifiers)} risk modifiers from {len(patient_variants)} variants")
        return risk_modifiers
    
    def get_variant_info(self, rsid: str) -> Optional[Dict]:
        """Get information about a specific variant."""
        if self.risk_data.empty:
            return None
        
        matches = self.risk_data[self.risk_data['rsid'].str.lower() == rsid.lower()]
        if matches.empty:
            return None
        
        row = matches.iloc[0]
        return {
            "rsid": row['rsid'],
            "gene": row.get('gene', 'Unknown'),
            "disease_id": row['disease_id'],
            "risk_allele": row.get('risk_allele', 'Unknown'),
            "risk_multiplier": float(row['risk_multiplier']),
            "population": row.get('population', 'Global')
        }
    
    def get_diseases_for_variant(self, rsid: str) -> List[str]:
        """Get all disease IDs associated with a variant."""
        if self.risk_data.empty:
            return []
        
        matches = self.risk_data[self.risk_data['rsid'].str.lower() == rsid.lower()]
        return matches['disease_id'].unique().tolist()


# Singleton instance
_genomic_instance: Optional[GenomicRiskEngine] = None


def get_genomic_risk_engine() -> GenomicRiskEngine:
    """Get or create the genomic risk engine instance."""
    global _genomic_instance
    if _genomic_instance is None:
        _genomic_instance = GenomicRiskEngine()
    return _genomic_instance
