"""
Treatment Recommendation Module.
Provides treatment recommendations based on confirmed diagnosis.
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import json
from pathlib import Path

from backend.config import settings
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


class Medication(BaseModel):
    """Medication recommendation."""
    name: str
    dosage: str
    frequency: str
    duration: str
    route: str = "oral"
    notes: Optional[str] = None


class TreatmentPlan(BaseModel):
    """Complete treatment recommendation."""
    disease_id: str
    disease_name: str
    severity: str = "moderate"
    medications: List[Medication] = Field(default_factory=list)
    lifestyle_modifications: List[str] = Field(default_factory=list)
    follow_up: str = "2 weeks"
    warnings: List[str] = Field(default_factory=list)
    referrals: List[str] = Field(default_factory=list)


# Treatment database - could be loaded from CSV/JSON in production
TREATMENT_DATABASE = {
    "D001": {  # Dengue Fever
        "disease_name": "Dengue Fever",
        "medications": [
            {"name": "Acetaminophen", "dosage": "500mg", "frequency": "every 6 hours", "duration": "5-7 days", "notes": "For fever and pain only"},
        ],
        "lifestyle_modifications": [
            "Complete bed rest",
            "Increase fluid intake (water, ORS, coconut water)",
            "Avoid aspirin and NSAIDs (bleeding risk)",
            "Monitor platelet count daily"
        ],
        "follow_up": "Daily monitoring during acute phase",
        "warnings": [
            "Watch for warning signs: abdominal pain, persistent vomiting, bleeding",
            "Seek emergency care if platelet count drops below 50,000"
        ]
    },
    "D002": {  # Influenza
        "disease_name": "Influenza",
        "medications": [
            {"name": "Oseltamivir (Tamiflu)", "dosage": "75mg", "frequency": "twice daily", "duration": "5 days", "notes": "Most effective if started within 48 hours"},
            {"name": "Acetaminophen", "dosage": "500-1000mg", "frequency": "every 6 hours", "duration": "as needed", "notes": "For fever and body aches"},
        ],
        "lifestyle_modifications": [
            "Rest and hydration",
            "Isolate from others for 5 days",
            "Use humidifier for congestion"
        ],
        "follow_up": "1 week if symptoms persist"
    },
    "D003": {  # Type 2 Diabetes
        "disease_name": "Type 2 Diabetes",
        "medications": [
            {"name": "Metformin", "dosage": "500mg", "frequency": "twice daily with meals", "duration": "ongoing", "notes": "Start low, increase gradually"},
        ],
        "lifestyle_modifications": [
            "Low glycemic index diet",
            "30 minutes moderate exercise 5x/week",
            "Regular blood glucose monitoring",
            "Weight management"
        ],
        "follow_up": "3 months for HbA1c recheck",
        "referrals": ["Diabetes educator", "Dietitian"]
    },
    "D006": {  # Malaria
        "disease_name": "Malaria",
        "medications": [
            {"name": "Artemether-Lumefantrine", "dosage": "4 tablets", "frequency": "twice daily", "duration": "3 days", "notes": "Take with fatty food"},
            {"name": "Primaquine", "dosage": "30mg", "frequency": "once daily", "duration": "14 days", "notes": "For P. vivax/ovale only, check G6PD first"},
        ],
        "lifestyle_modifications": [
            "Rest and hydration",
            "Use mosquito nets",
            "Complete full course even if feeling better"
        ],
        "follow_up": "24-48 hours to confirm parasite clearance",
        "warnings": [
            "Monitor for signs of severe malaria",
            "Return immediately if condition worsens"
        ]
    },
    "D009": {  # Tuberculosis
        "disease_name": "Tuberculosis",
        "medications": [
            {"name": "Isoniazid (INH)", "dosage": "300mg", "frequency": "once daily", "duration": "6 months", "notes": "Take with pyridoxine 25mg"},
            {"name": "Rifampicin", "dosage": "600mg", "frequency": "once daily", "duration": "6 months", "notes": "Take on empty stomach"},
            {"name": "Pyrazinamide", "dosage": "1500mg", "frequency": "once daily", "duration": "2 months"},
            {"name": "Ethambutol", "dosage": "1200mg", "frequency": "once daily", "duration": "2 months"},
        ],
        "lifestyle_modifications": [
            "Respiratory isolation for first 2 weeks",
            "Good nutrition",
            "Avoid alcohol",
            "Ensure medication adherence"
        ],
        "follow_up": "Monthly liver function tests",
        "referrals": ["TB specialist", "Contact tracing for close contacts"]
    },
    "D012": {  # Rheumatoid Arthritis
        "disease_name": "Rheumatoid Arthritis",
        "medications": [
            {"name": "Methotrexate", "dosage": "7.5-15mg", "frequency": "once weekly", "duration": "ongoing", "notes": "Take folic acid 1mg daily except on MTX day"},
            {"name": "NSAIDs (Naproxen)", "dosage": "500mg", "frequency": "twice daily", "duration": "as needed", "notes": "For symptom relief"},
        ],
        "lifestyle_modifications": [
            "Regular low-impact exercise",
            "Joint protection techniques",
            "Hot/cold therapy for flares"
        ],
        "follow_up": "6 weeks to assess response",
        "referrals": ["Rheumatologist", "Physical therapist"]
    },
    "D017": {  # Pneumonia
        "disease_name": "Pneumonia",
        "medications": [
            {"name": "Amoxicillin-Clavulanate", "dosage": "625mg", "frequency": "three times daily", "duration": "7 days", "notes": "Community-acquired, non-severe"},
            {"name": "Azithromycin", "dosage": "500mg day 1, then 250mg", "frequency": "once daily", "duration": "5 days", "notes": "Add for atypical coverage"},
        ],
        "lifestyle_modifications": [
            "Rest",
            "Increase fluid intake",
            "Deep breathing exercises"
        ],
        "follow_up": "48-72 hours if no improvement",
        "warnings": ["Seek emergency care if breathing difficulty worsens"]
    }
}


class TreatmentRecommender:
    """Recommends treatment based on diagnosis."""
    
    def __init__(self):
        self.treatments = TREATMENT_DATABASE
        logger.info(f"TreatmentRecommender initialized with {len(self.treatments)} treatment protocols")
    
    def get_treatment(
        self,
        disease_id: str,
        severity: str = "moderate",
        contraindications: Optional[List[str]] = None
    ) -> Optional[TreatmentPlan]:
        """
        Get treatment recommendation for a disease.
        
        Args:
            disease_id: Disease identifier
            severity: mild/moderate/severe
            contraindications: List of contraindicated drugs
            
        Returns:
            TreatmentPlan or None if disease not in database
        """
        if disease_id not in self.treatments:
            logger.warning(f"No treatment protocol for disease: {disease_id}")
            return None
        
        treatment_data = self.treatments[disease_id].copy()
        
        # Convert medication dicts to Medication objects
        medications = []
        for med in treatment_data.get("medications", []):
            # Filter out contraindicated medications
            if contraindications and med["name"].lower() in [c.lower() for c in contraindications]:
                logger.info(f"Excluding contraindicated medication: {med['name']}")
                continue
            medications.append(Medication(**med))
        
        plan = TreatmentPlan(
            disease_id=disease_id,
            disease_name=treatment_data["disease_name"],
            severity=severity,
            medications=medications,
            lifestyle_modifications=treatment_data.get("lifestyle_modifications", []),
            follow_up=treatment_data.get("follow_up", "2 weeks"),
            warnings=treatment_data.get("warnings", []),
            referrals=treatment_data.get("referrals", [])
        )
        
        logger.info(f"Generated treatment plan for {disease_id}: {len(medications)} medications")
        return plan
    
    def get_all_disease_ids(self) -> List[str]:
        """Get list of diseases with available treatments."""
        return list(self.treatments.keys())


# Singleton instance
_recommender: Optional[TreatmentRecommender] = None


def get_treatment_recommender() -> TreatmentRecommender:
    """Get or create TreatmentRecommender instance."""
    global _recommender
    if _recommender is None:
        _recommender = TreatmentRecommender()
    return _recommender
