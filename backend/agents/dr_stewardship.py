"""
Dr. Stewardship Agent - Evaluates test cost-effectiveness and vetoes unnecessary tests.
Ensures diagnostic workup stays within budget while maintaining clinical quality.
"""
from typing import List, Optional, Tuple
import json

from backend.models.diagnosis import Hypothesis, DiagnosticState
from backend.models.test_order import Test, TestRequest
from backend.utils.llm_client import LLMClient, get_llm_client
from backend.utils.logging_config import get_logger, get_agent_logger

logger = get_logger(__name__)
agent_logger = get_agent_logger("Dr.Stewardship")


STEWARDSHIP_SYSTEM_PROMPT = """You are Dr. Stewardship, a clinical cost-effectiveness specialist.

Your role is to evaluate proposed diagnostic tests and ensure they are clinically necessary and cost-effective.

Consider:
1. Is this test truly needed given current evidence?
2. Could a cheaper alternative provide similar information?
3. Is the expected information gain worth the cost?
4. Are we approaching high confidence and this test may be unnecessary?

Be concise. Respond with JSON only."""


STEWARDSHIP_PROMPT_TEMPLATE = """Evaluate this proposed test:

TEST: {test_name}
COST: ${test_cost}
EXPECTED INFO GAIN: {info_gain:.3f} bits

CURRENT TOP HYPOTHESES:
{top_hypotheses}

CURRENT CONFIDENCE: {confidence:.1%}
BUDGET REMAINING: ${budget_remaining}
TESTS ALREADY DONE: {completed_tests}

Should this test be approved?

Respond with JSON:
{{
  "approved": true/false,
  "rationale": "Brief explanation",
  "alternative_test_id": null or "T00X" if suggesting alternative
}}"""


class DrStewardship:
    """
    Agent responsible for clinical resource stewardship.
    Vetoes unnecessary or cost-ineffective tests.
    """
    
    # Minimum info gain threshold (bits)
    MIN_INFO_GAIN = 0.05
    
    # Cost per bit threshold (above this, scrutinize more)
    MAX_COST_PER_BIT = 500
    
    # Confidence threshold above which to be more conservative
    HIGH_CONFIDENCE_THRESHOLD = 0.75
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        use_llm: bool = False
    ):
        self.llm = llm_client or get_llm_client()
        self.use_llm = use_llm  # Use LLM for complex decisions
        logger.info("Dr. Stewardship agent initialized")
    
    def evaluate_test(
        self,
        test_request: TestRequest,
        state: DiagnosticState
    ) -> Tuple[bool, str]:
        """
        Evaluate whether a proposed test should be approved.
        
        Args:
            test_request: The proposed test
            state: Current diagnostic state
            
        Returns:
            Tuple of (approved: bool, rationale: str)
        """
        test = test_request.test
        info_gain = test_request.expected_information_gain
        
        agent_logger.info(
            f"Evaluating: {test.name} (${test.cost_usd}, {info_gain:.3f} bits)"
        )
        
        # Rule 1: Budget check
        if test.cost_usd > state.budget_remaining:
            rationale = f"Test exceeds remaining budget (${state.budget_remaining})"
            agent_logger.info(f"VETOED - {rationale}")
            return False, rationale
        
        # Rule 2: Minimum info gain
        if info_gain < self.MIN_INFO_GAIN:
            rationale = f"Expected info gain ({info_gain:.3f}) below minimum threshold"
            agent_logger.info(f"VETOED - {rationale}")
            return False, rationale
        
        # Rule 3: Cost/benefit ratio
        cost_per_bit = test.cost_usd / max(info_gain, 0.001)
        if cost_per_bit > self.MAX_COST_PER_BIT and state.confidence < self.HIGH_CONFIDENCE_THRESHOLD:
            rationale = f"Cost per bit (${cost_per_bit:.0f}) exceeds threshold"
            agent_logger.info(f"VETOED - {rationale}")
            return False, rationale
        
        # Rule 4: High confidence - be conservative
        if state.confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            # Only approve high-value tests at high confidence
            if info_gain < 0.2 or cost_per_bit > 200:
                rationale = f"Confidence already high ({state.confidence:.1%}); test may be unnecessary"
                agent_logger.info(f"VETOED - {rationale}")
                return False, rationale
        
        # Rule 5: Avoid duplicate coverage
        for completed_test_id in state.completed_tests:
            if self._tests_redundant(test.test_id, completed_test_id):
                rationale = f"Similar test already performed ({completed_test_id})"
                agent_logger.info(f"VETOED - {rationale}")
                return False, rationale
        
        # Approved
        rationale = (
            f"Approved: ${test.cost_usd} for {info_gain:.2f} bits info gain "
            f"(${cost_per_bit:.0f}/bit). Budget remaining: ${state.budget_remaining - test.cost_usd}"
        )
        agent_logger.info(f"APPROVED - {test.name}")
        return True, rationale
    
    async def evaluate_test_with_llm(
        self,
        test_request: TestRequest,
        state: DiagnosticState
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Use LLM for more nuanced test evaluation.
        
        Returns:
            Tuple of (approved, rationale, alternative_test_id)
        """
        test = test_request.test
        
        # Format top hypotheses
        top_hyp_str = "\n".join([
            f"  - {h.disease.name}: {h.probability:.1%}"
            for h in state.hypotheses[:5]
        ])
        
        prompt = STEWARDSHIP_PROMPT_TEMPLATE.format(
            test_name=test.name,
            test_cost=test.cost_usd,
            info_gain=test_request.expected_information_gain,
            top_hypotheses=top_hyp_str,
            confidence=state.confidence,
            budget_remaining=state.budget_remaining,
            completed_tests=", ".join(state.completed_tests) or "None"
        )
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=STEWARDSHIP_SYSTEM_PROMPT,
                json_mode=True
            )
            
            # Parse response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            data = json.loads(response)
            
            return (
                data.get('approved', True),
                data.get('rationale', 'No rationale provided'),
                data.get('alternative_test_id')
            )
            
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            # Fall back to rule-based
            approved, rationale = self.evaluate_test(test_request, state)
            return approved, rationale, None
    
    def _tests_redundant(self, test_id_1: str, test_id_2: str) -> bool:
        """Check if two tests provide redundant information."""
        # Simple heuristic: same category and overlapping diseases
        # Could be enhanced with actual test metadata
        
        # For now, only flag exact duplicates
        return test_id_1 == test_id_2
    
    def suggest_alternative(
        self,
        vetoed_test: Test,
        available_tests: List[Test],
        state: DiagnosticState
    ) -> Optional[Test]:
        """
        Suggest a cheaper alternative to a vetoed test.
        
        Args:
            vetoed_test: The test that was vetoed
            available_tests: List of available alternatives
            state: Current diagnostic state
            
        Returns:
            Alternative test if found, None otherwise
        """
        alternatives = []
        
        for test in available_tests:
            if test.test_id == vetoed_test.test_id:
                continue
            if test.test_id in state.completed_tests:
                continue
            if test.cost_usd >= vetoed_test.cost_usd:
                continue
            if test.cost_usd > state.budget_remaining:
                continue
            
            # Check if test can detect similar diseases
            overlap = set(test.diseases_detected) & set(vetoed_test.diseases_detected)
            if overlap:
                alternatives.append((test, len(overlap)))
        
        if not alternatives:
            return None
        
        # Return the cheapest alternative with most overlap
        alternatives.sort(key=lambda x: (-x[1], x[0].cost_usd))
        return alternatives[0][0]


def get_dr_stewardship(
    llm_client: Optional[LLMClient] = None,
    use_llm: bool = False
) -> DrStewardship:
    """Get Dr. Stewardship agent instance."""
    return DrStewardship(llm_client, use_llm)
