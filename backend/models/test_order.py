"""
Pydantic models for medical tests and results.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class Test(BaseModel):
    """A diagnostic test from the knowledge base."""
    test_id: str
    name: str
    category: str = Field(default="Blood", description="Test category: Blood, Imaging, etc.")
    cost_usd: float = Field(default=50.0, ge=0)
    turnaround_hours: float = Field(default=24, ge=0)
    sensitivity: float = Field(default=0.85, ge=0, le=1)
    specificity: float = Field(default=0.85, ge=0, le=1)
    diseases_detected: List[str] = Field(default_factory=list, description="disease_ids this test can detect")


class TestRequest(BaseModel):
    """A request for a diagnostic test."""
    test: Test
    rationale: str = Field(..., description="Why this test is recommended")
    expected_information_gain: float = Field(default=0.0, description="Expected entropy reduction")
    urgency: str = Field(default="routine", pattern="^(stat|urgent|routine)$")


class TestResult(BaseModel):
    """Result of a diagnostic test."""
    test_id: str
    result: str = Field(..., description="positive, negative, or specific value")
    value: Optional[float] = Field(None, description="Numeric value if applicable")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    reference_range: Optional[str] = Field(None, description="Normal range")
    interpretation: Optional[str] = Field(None, description="Clinical interpretation")
    
    @property
    def is_positive(self) -> bool:
        return self.result.lower() in ["positive", "detected", "abnormal", "high", "low"]
    
    @property
    def is_negative(self) -> bool:
        return self.result.lower() in ["negative", "not detected", "normal", "within range"]


class TestCatalog(BaseModel):
    """Collection of available tests."""
    tests: List[Test] = Field(default_factory=list)
    
    def get_by_id(self, test_id: str) -> Optional[Test]:
        """Get a test by its ID."""
        for test in self.tests:
            if test.test_id == test_id:
                return test
        return None
    
    def get_tests_for_disease(self, disease_id: str) -> List[Test]:
        """Get all tests that can detect a specific disease."""
        return [t for t in self.tests if disease_id in t.diseases_detected]
    
    def get_by_category(self, category: str) -> List[Test]:
        """Get tests by category."""
        return [t for t in self.tests if t.category.lower() == category.lower()]
