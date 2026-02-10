"""
Epidemiological priors from local CSV data with optional API enrichment.
Provides regional/seasonal disease prevalence probabilities.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from backend.config import settings
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class EpidemiologicalPriors:
    """
    Load and query disease prevalence data from CSV files.
    Optionally fetches from WHO GHO API if enabled.
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        use_api: bool = False
    ):
        self.data_dir = data_dir or settings.epidemiology_dir
        self.use_api = use_api and settings.api.use_external_apis
        
        # Load CSV data
        self._load_data()
        logger.info(f"EpidemiologicalPriors initialized with {len(self.prevalence)} prevalence records")
    
    def _load_data(self):
        """Load prevalence and seasonal data from CSV files."""
        prevalence_path = self.data_dir / "disease_prevalence.csv"
        seasonal_path = self.data_dir / "seasonal_patterns.csv"
        
        if not prevalence_path.exists():
            logger.warning(f"Prevalence file not found: {prevalence_path}")
            self.prevalence = pd.DataFrame()
        else:
            self.prevalence = pd.read_csv(prevalence_path)
            logger.debug(f"Loaded {len(self.prevalence)} prevalence records")
        
        if not seasonal_path.exists():
            logger.warning(f"Seasonal patterns file not found: {seasonal_path}")
            self.seasonal = pd.DataFrame()
        else:
            self.seasonal = pd.read_csv(seasonal_path)
            logger.debug(f"Loaded {len(self.seasonal)} seasonal patterns")
    
    def get_priors(
        self,
        region: str = "Global",
        month: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Get disease priors based on region and optional seasonal adjustments.
        
        Args:
            region: Geographic region (e.g., "South Asia", "Global")
            month: Month 1-12 for seasonal adjustment
            
        Returns:
            Dictionary mapping disease_id to prior probability
        """
        if month is None:
            month = datetime.now().month
        
        priors: Dict[str, float] = {}
        
        # Get base prevalence for region
        region_data = self.prevalence[
            self.prevalence['region'].str.contains(region, case=False, na=False)
        ] if not self.prevalence.empty else pd.DataFrame()
        
        # Fall back to global if region not found
        if region_data.empty and not self.prevalence.empty:
            region_data = self.prevalence[
                self.prevalence['region'].str.contains("Global", case=False, na=False)
            ]
        
        # Convert prevalence per 100k to probability
        for _, row in region_data.iterrows():
            disease_id = row['disease_id']
            prevalence = row['prevalence_per_100k']
            # Convert to probability (per 100k -> fraction)
            base_prob = prevalence / 100000.0
            priors[disease_id] = base_prob
        
        # Apply seasonal multipliers
        if not self.seasonal.empty and month:
            seasonal_month = self.seasonal[self.seasonal['month'] == month]
            for _, row in seasonal_month.iterrows():
                disease_id = row['disease_id']
                multiplier = row['multiplier']
                if disease_id in priors:
                    priors[disease_id] *= multiplier
                    logger.debug(f"Applied seasonal multiplier {multiplier} to {disease_id}")
        
        logger.info(f"Generated {len(priors)} priors for region={region}, month={month}")
        return priors
    
    def get_disease_prevalence(self, disease_id: str, region: str = "Global") -> float:
        """Get prevalence for a specific disease in a region."""
        if self.prevalence.empty:
            return 0.0
        
        match = self.prevalence[
            (self.prevalence['disease_id'] == disease_id) &
            (self.prevalence['region'].str.contains(region, case=False, na=False))
        ]
        
        if not match.empty:
            return float(match.iloc[0]['prevalence_per_100k'])
        return 0.0
    
    def get_seasonal_multiplier(self, disease_id: str, month: int) -> float:
        """Get seasonal multiplier for a specific disease and month."""
        if self.seasonal.empty:
            return 1.0
        
        match = self.seasonal[
            (self.seasonal['disease_id'] == disease_id) &
            (self.seasonal['month'] == month)
        ]
        
        if not match.empty:
            return float(match.iloc[0]['multiplier'])
        return 1.0


# Singleton instance
_priors_instance: Optional[EpidemiologicalPriors] = None


def get_epidemiological_priors() -> EpidemiologicalPriors:
    """Get or create the epidemiological priors instance."""
    global _priors_instance
    if _priors_instance is None:
        _priors_instance = EpidemiologicalPriors()
    return _priors_instance
