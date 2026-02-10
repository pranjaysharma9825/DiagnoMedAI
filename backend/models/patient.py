"""
Pydantic models for patient data and medical records.
"""
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class PatientDemographics(BaseModel):
    """Basic demographic information about a patient."""
    patient_id: str = Field(..., description="Unique patient identifier")
    age: int = Field(..., ge=0, le=150, description="Patient age in years")
    sex: str = Field(..., pattern="^(male|female|other)$", description="Biological sex")
    region: str = Field(default="Global", description="Geographic region for epidemiological priors")


class GeneticVariant(BaseModel):
    """A genetic variant reported by the patient or from testing."""
    rsid: str = Field(..., description="SNP reference ID, e.g., rs1234567")
    gene: Optional[str] = Field(None, description="Gene name if known")
    allele: Optional[str] = Field(None, description="Risk allele if known")


class PatientProfile(BaseModel):
    """Complete patient profile including demographics and genetic information."""
    demographics: PatientDemographics
    genetic_variants: List[GeneticVariant] = Field(default_factory=list)
    medical_history: List[str] = Field(default_factory=list, description="List of known conditions")
    current_medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    
    @property
    def patient_id(self) -> str:
        return self.demographics.patient_id
    
    @property
    def age(self) -> int:
        return self.demographics.age
    
    @property
    def region(self) -> str:
        return self.demographics.region


class SymptomReport(BaseModel):
    """A symptom reported by the patient."""
    symptom_id: Optional[str] = Field(None, description="ID if matched to known symptom")
    name: str = Field(..., description="Symptom name or description")
    severity: int = Field(default=5, ge=1, le=10, description="Severity 1-10")
    duration_days: Optional[int] = Field(None, description="How long symptom present")
    onset: Optional[str] = Field(None, description="When symptom started: acute, gradual, chronic")


class PatientCase(BaseModel):
    """A complete patient case for diagnosis."""
    profile: PatientProfile
    symptoms: List[SymptomReport]
    chief_complaint: str = Field(..., description="Primary reason for visit")
    visit_date: date = Field(default_factory=date.today)
    
    @property
    def patient_id(self) -> str:
        return self.profile.patient_id
