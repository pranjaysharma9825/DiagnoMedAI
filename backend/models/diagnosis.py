"""
Pydantic models for diagnosis-related data structures.
"""
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class Disease(BaseModel):
    """A disease from the knowledge base."""
    disease_id: str
    name: str
    icd10_code: Optional[str] = None
    category: Optional[str] = None
    severity: int = Field(default=3, ge=1, le=5)
    description: Optional[str] = None
    typical_duration_days: int = Field(default=-1, description="-1 means chronic/lifelong")


class Hypothesis(BaseModel):
    """A diagnostic hypothesis with probability."""
    disease: Disease
    probability: float = Field(..., ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    rule_out_criteria: List[str] = Field(default_factory=list)
    
    def __lt__(self, other: "Hypothesis") -> bool:
        """Sort by probability descending."""
        return self.probability > other.probability


class DiagnosticState(BaseModel):
    """
    Current state of the diagnostic process.
    Used by LangGraph for state management.
    """
    patient_id: str
    symptoms: List[str] = Field(default_factory=list)
    symptom_ids: List[str] = Field(default_factory=list)
    
    # Prior probabilities from epidemiology/genomics
    priors: Dict[str, float] = Field(default_factory=dict, description="disease_id -> prior P(disease)")
    
    # Current differential diagnosis
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    
    # Tests
    pending_tests: List[str] = Field(default_factory=list, description="test_ids awaiting results")
    completed_tests: List[str] = Field(default_factory=list, description="test_ids with results")
    test_results: Dict[str, str] = Field(default_factory=dict, description="test_id -> result")
    
    # Budget tracking
    budget_remaining: float = Field(default=5000.0)
    total_cost: float = Field(default=0.0)
    
    # Confidence
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    iteration: int = Field(default=0)
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def top_hypothesis(self) -> Optional[Hypothesis]:
        """Get the most likely diagnosis."""
        if not self.hypotheses:
            return None
        return max(self.hypotheses, key=lambda h: h.probability)
    
    def update_confidence(self):
        """Update confidence based on top hypothesis probability."""
        if self.top_hypothesis:
            self.confidence = self.top_hypothesis.probability
        self.updated_at = datetime.now()


class DiagnosisResult(BaseModel):
    """Final diagnosis result after confidence threshold reached."""
    patient_id: str
    final_diagnosis: Disease
    confidence: float
    differential: List[Hypothesis] = Field(default_factory=list, description="Other considered diagnoses")
    tests_ordered: List[str] = Field(default_factory=list)
    total_cost: float = Field(default=0.0)
    iterations: int = Field(default=1)
    reasoning_trace: List[str] = Field(default_factory=list)
    diagnosed_at: datetime = Field(default_factory=datetime.now)
