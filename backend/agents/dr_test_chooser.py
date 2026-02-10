"""
Dr. Test-Chooser Agent - Recommends diagnostic tests based on entropy reduction.
Selects tests that maximize information gain for the differential diagnosis.
"""
from typing import List, Optional, Dict
import math
import pandas as pd
from pathlib import Path

from backend.models.diagnosis import Hypothesis, DiagnosticState
from backend.models.test_order import Test, TestRequest, TestCatalog
from backend.config import settings
from backend.utils.llm_client import LLMClient, get_llm_client
from backend.utils.logging_config import get_logger, get_agent_logger

logger = get_logger(__name__)
agent_logger = get_agent_logger("Dr.TestChooser")


class DrTestChooser:
    """
    Agent responsible for recommending optimal diagnostic tests.
    Uses entropy-based information gain to prioritize tests.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_llm_client()
        self.test_catalog = self._load_test_catalog()
        logger.info(f"Dr. Test-Chooser initialized with {len(self.test_catalog.tests)} tests")
    
    def _load_test_catalog(self) -> TestCatalog:
        """Load test catalog from CSV."""
        tests_path = settings.knowledge_dir / "tests.csv"
        
        if not tests_path.exists():
            logger.warning(f"Tests file not found: {tests_path}")
            return TestCatalog(tests=[])
        
        df = pd.read_csv(tests_path)
        tests = []
        
        for _, row in df.iterrows():
            # Parse diseases_detected (comma-separated)
            diseases = []
            if pd.notna(row.get('diseases_detected', '')):
                diseases = [d.strip() for d in str(row['diseases_detected']).split(',')]
            
            test = Test(
                test_id=row['test_id'],
                name=row['name'],
                category=row.get('category', 'Blood'),
                cost_usd=float(row.get('cost_usd', 50)),
                turnaround_hours=float(row.get('turnaround_hours', 24)),
                sensitivity=float(row.get('sensitivity', 0.85)),
                specificity=float(row.get('specificity', 0.85)),
                diseases_detected=diseases
            )
            tests.append(test)
        
        return TestCatalog(tests=tests)
    
    def compute_entropy(self, hypotheses: List[Hypothesis]) -> float:
        """
        Compute Shannon entropy of the current hypothesis distribution.
        H(Φ) = -Σ P(d) * log2(P(d))
        """
        if not hypotheses:
            return 0.0
        
        entropy = 0.0
        for hyp in hypotheses:
            if hyp.probability > 0:
                entropy -= hyp.probability * math.log2(hyp.probability)
        
        return entropy
    
    def estimate_posterior(
        self,
        hypothesis: Hypothesis,
        test: Test,
        result_positive: bool
    ) -> float:
        """
        Estimate posterior probability after test result using Bayes' theorem.
        P(D|T+) = P(T+|D) * P(D) / P(T+)
        """
        prior = hypothesis.probability
        disease_id = hypothesis.disease.disease_id
        
        # Check if test detects this disease
        if disease_id in test.diseases_detected:
            if result_positive:
                # True positive: P(T+|D) = sensitivity
                likelihood = test.sensitivity
            else:
                # False negative: P(T-|D) = 1 - sensitivity
                likelihood = 1 - test.sensitivity
        else:
            if result_positive:
                # False positive: P(T+|¬D) = 1 - specificity
                likelihood = 1 - test.specificity
            else:
                # True negative: P(T-|¬D) = specificity
                likelihood = test.specificity
        
        # Simplified posterior (not normalized, for relative comparison)
        return likelihood * prior
    
    def compute_expected_entropy_reduction(
        self,
        test: Test,
        hypotheses: List[Hypothesis]
    ) -> float:
        """
        Compute expected entropy reduction from a test.
        ΔH = H(Φ) - E[H(Φ|T)]
        
        where E[H(Φ|T)] = P(T+) * H(Φ|T+) + P(T-) * H(Φ|T-)
        """
        current_entropy = self.compute_entropy(hypotheses)
        
        if current_entropy == 0:
            return 0.0
        
        # Estimate P(T+) based on which hypotheses the test can detect
        p_positive = 0.0
        for hyp in hypotheses:
            if hyp.disease.disease_id in test.diseases_detected:
                p_positive += hyp.probability * test.sensitivity
            else:
                p_positive += hyp.probability * (1 - test.specificity)
        
        p_negative = 1 - p_positive
        
        # Compute posterior hypotheses for positive result
        posteriors_positive = []
        posteriors_negative = []
        
        for hyp in hypotheses:
            post_pos = self.estimate_posterior(hyp, test, result_positive=True)
            post_neg = self.estimate_posterior(hyp, test, result_positive=False)
            
            posteriors_positive.append(Hypothesis(
                disease=hyp.disease,
                probability=post_pos
            ))
            posteriors_negative.append(Hypothesis(
                disease=hyp.disease,
                probability=post_neg
            ))
        
        # Normalize posteriors
        sum_pos = sum(h.probability for h in posteriors_positive)
        sum_neg = sum(h.probability for h in posteriors_negative)
        
        if sum_pos > 0:
            for h in posteriors_positive:
                h.probability /= sum_pos
        if sum_neg > 0:
            for h in posteriors_negative:
                h.probability /= sum_neg
        
        # Compute conditional entropies
        h_given_positive = self.compute_entropy(posteriors_positive)
        h_given_negative = self.compute_entropy(posteriors_negative)
        
        # Expected entropy after test
        expected_entropy = p_positive * h_given_positive + p_negative * h_given_negative
        
        # Information gain
        return current_entropy - expected_entropy
    
    def select_next_test(
        self,
        state: DiagnosticState,
        max_cost: Optional[float] = None
    ) -> Optional[TestRequest]:
        """
        Select the best test based on expected information gain.
        
        Args:
            state: Current diagnostic state with hypotheses
            max_cost: Optional budget constraint
            
        Returns:
            TestRequest for the recommended test, or None if no suitable test
        """
        agent_logger.info(f"Selecting next test. Budget remaining: ${state.budget_remaining}")
        
        if not state.hypotheses:
            logger.warning("No hypotheses to test against")
            return None
        
        cost_limit = max_cost or state.budget_remaining
        
        # Filter out already-completed tests
        available_tests = [
            t for t in self.test_catalog.tests
            if t.test_id not in state.completed_tests
            and t.cost_usd <= cost_limit
        ]
        
        if not available_tests:
            logger.warning("No available tests within budget")
            return None
        
        # Score each test by information gain / cost ratio
        scored_tests = []
        for test in available_tests:
            info_gain = self.compute_expected_entropy_reduction(test, state.hypotheses)
            # Value = info gain per dollar (cost-effectiveness)
            value = info_gain / max(test.cost_usd, 1.0)
            scored_tests.append((test, info_gain, value))
        
        # Sort by value (info gain per dollar)
        scored_tests.sort(key=lambda x: x[2], reverse=True)
        
        if not scored_tests:
            return None
        
        best_test, best_gain, best_value = scored_tests[0]
        
        agent_logger.info(
            f"Recommended: {best_test.name} (${best_test.cost_usd}) "
            f"- Expected info gain: {best_gain:.3f} bits"
        )
        
        # Build rationale
        top_diseases = [h.disease.name for h in state.hypotheses[:3]]
        rationale = (
            f"Test '{best_test.name}' selected for maximum information gain "
            f"({best_gain:.2f} bits). Can help differentiate between: {', '.join(top_diseases)}. "
            f"Cost: ${best_test.cost_usd}"
        )
        
        return TestRequest(
            test=best_test,
            rationale=rationale,
            expected_information_gain=best_gain,
            urgency="routine"
        )
    
    def get_tests_for_disease(self, disease_id: str) -> List[Test]:
        """Get all tests that can detect a specific disease."""
        return self.test_catalog.get_tests_for_disease(disease_id)


def get_dr_test_chooser(llm_client: Optional[LLMClient] = None) -> DrTestChooser:
    """Get Dr. Test-Chooser agent instance."""
    return DrTestChooser(llm_client)
