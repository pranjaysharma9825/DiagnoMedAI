"""
Dr. Hypothesis Agent - Maintains and updates the differential diagnosis.
Uses Bayesian reasoning to update disease probabilities based on evidence.
"""
from typing import List, Dict, Optional
import json

from backend.models.diagnosis import Hypothesis, Disease, DiagnosticState
from backend.priors.symptom_disease_map import get_symptom_disease_mapper
from backend.priors.epidemiology import get_epidemiological_priors
from backend.priors.genphire import get_genomic_risk_engine
from backend.utils.llm_client import LLMClient, get_llm_client
from backend.utils.logging_config import get_logger, get_agent_logger

logger = get_logger(__name__)
agent_logger = get_agent_logger("Dr.Hypothesis")


HYPOTHESIS_SYSTEM_PROMPT = """You are Dr. Hypothesis, a clinical reasoning specialist focused on differential diagnosis.

Your task is to analyze patient symptoms and evidence to generate and rank diagnostic hypotheses.

Rules:
1. Consider all provided symptoms, priors, and test results
2. Generate 5-7 most likely diagnoses
3. Assign probabilities that sum to at most 0.95 (leave room for unknown)
4. Provide brief supporting and contradicting evidence for each
5. Be concise - minimize token usage

Respond ONLY with valid JSON."""


HYPOTHESIS_PROMPT_TEMPLATE = """Analyze this case and provide differential diagnosis:

SYMPTOMS: {symptoms}

EPIDEMIOLOGICAL CONTEXT:
- Region: {region}
- High-prevalence diseases: {high_prevalence}

GENETIC RISK FACTORS: {genetic_risks}

PREVIOUS TEST RESULTS: {test_results}

Generate a JSON array with format:
[
  {{
    "disease_id": "D001",
    "disease_name": "Disease Name",
    "probability": 0.35,
    "supporting": ["symptom1 matches", "high regional prevalence"],
    "contradicting": ["age atypical"],
    "rule_out_tests": ["T001", "T002"]
  }}
]

Rank by probability, most likely first. Include 5-7 hypotheses."""


class DrHypothesis:
    """
    Agent responsible for maintaining the differential diagnosis.
    Uses LLM for clinical reasoning and Bayesian updates.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or get_llm_client()
        self.mapper = get_symptom_disease_mapper()
        self.epi_priors = get_epidemiological_priors()
        self.genomic_engine = get_genomic_risk_engine()
        logger.info("Dr. Hypothesis agent initialized")
    
    async def generate_initial_ddx(
        self,
        symptoms: List[str],
        region: str = "Global",
        genetic_variants: List[str] = None
    ) -> List[Hypothesis]:
        """
        Generate initial differential diagnosis from symptoms.
        
        Args:
            symptoms: List of symptom names
            region: Geographic region for epi priors
            genetic_variants: Optional list of rsIDs
            
        Returns:
            List of Hypothesis objects ranked by probability
        """
        agent_logger.info(f"Generating initial DDx for symptoms: {symptoms}")
        
        # Get priors
        epi_priors = self.epi_priors.get_priors(region=region)
        high_prevalence = sorted(
            epi_priors.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        high_prevalence_str = ", ".join([f"{d}: {p:.4f}" for d, p in high_prevalence])
        
        # Get genetic risks
        genetic_risks = {}
        if genetic_variants:
            genetic_risks = self.genomic_engine.get_risk_modifiers(genetic_variants)
        genetic_risks_str = json.dumps(genetic_risks) if genetic_risks else "None reported"
        
        # Build prompt
        prompt = HYPOTHESIS_PROMPT_TEMPLATE.format(
            symptoms=", ".join(symptoms),
            region=region,
            high_prevalence=high_prevalence_str,
            genetic_risks=genetic_risks_str,
            test_results="No tests performed yet"
        )
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=HYPOTHESIS_SYSTEM_PROMPT,
                json_mode=True
            )
            
            hypotheses = self._parse_response(response)
            agent_logger.info(f"Generated {len(hypotheses)} initial hypotheses")
            return hypotheses
            
        except Exception as e:
            logger.error(f"Error generating DDx: {e}")
            # Fallback to rule-based candidates
            return self._fallback_ddx(symptoms, epi_priors, genetic_risks)
    
    async def update_ddx(
        self,
        state: DiagnosticState,
        new_test_result: Dict[str, str]
    ) -> List[Hypothesis]:
        """
        Update differential diagnosis with new test results.
        
        Args:
            state: Current diagnostic state
            new_test_result: Dict with test_id -> result
            
        Returns:
            Updated list of hypotheses
        """
        agent_logger.info(f"Updating DDx with new test results: {new_test_result}")
        
        # Merge test results
        all_results = {**state.test_results, **new_test_result}
        test_results_str = json.dumps(all_results) if all_results else "None"
        
        # Get priors
        high_prevalence = sorted(
            state.priors.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        high_prevalence_str = ", ".join([f"{d}: {p:.4f}" for d, p in high_prevalence])
        
        prompt = HYPOTHESIS_PROMPT_TEMPLATE.format(
            symptoms=", ".join(state.symptoms),
            region="Global",
            high_prevalence=high_prevalence_str,
            genetic_risks="Previously applied",
            test_results=test_results_str
        )
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=HYPOTHESIS_SYSTEM_PROMPT,
                json_mode=True
            )
            
            hypotheses = self._parse_response(response)
            agent_logger.info(f"Updated to {len(hypotheses)} hypotheses after test results")
            return hypotheses
            
        except Exception as e:
            logger.error(f"Error updating DDx: {e}")
            return state.hypotheses
    
    def _parse_response(self, response: str) -> List[Hypothesis]:
        """Parse LLM response into Hypothesis objects."""
        try:
            # Extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            data = json.loads(response)
            
            hypotheses = []
            for item in data:
                disease = Disease(
                    disease_id=item.get('disease_id', 'UNKNOWN'),
                    name=item.get('disease_name', 'Unknown Disease'),
                )
                
                hypothesis = Hypothesis(
                    disease=disease,
                    probability=float(item.get('probability', 0.1)),
                    supporting_evidence=item.get('supporting', []),
                    contradicting_evidence=item.get('contradicting', []),
                    rule_out_criteria=item.get('rule_out_tests', [])
                )
                hypotheses.append(hypothesis)
            
            # Sort by probability
            hypotheses.sort(key=lambda h: h.probability, reverse=True)
            return hypotheses
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []
    
    def _fallback_ddx(
        self,
        symptoms: List[str],
        epi_priors: Dict[str, float],
        genetic_risks: Dict[str, float]
    ) -> List[Hypothesis]:
        """Generate fallback DDx using rule-based approach."""
        logger.info("Using fallback rule-based DDx generation")
        
        candidates = self.mapper.get_candidates(symptoms, top_k=7)
        hypotheses = []
        
        for i, candidate in enumerate(candidates):
            disease_id = candidate['disease_id']
            base_prob = candidate['base_probability']
            
            # Apply priors
            if disease_id in epi_priors:
                base_prob *= (1 + min(epi_priors[disease_id] * 1000, 1.0))
            
            # Apply genetic risks
            if disease_id in genetic_risks:
                base_prob *= genetic_risks[disease_id]
            
            # Normalize to max 0.9
            base_prob = min(base_prob, 0.9 - i * 0.1)
            
            disease = self.mapper.get_disease_model(disease_id)
            if disease:
                hypotheses.append(Hypothesis(
                    disease=disease,
                    probability=max(base_prob, 0.01),
                    supporting_evidence=[f"Matches {candidate['matching_symptoms']} symptoms"]
                ))
        
        return hypotheses


def get_dr_hypothesis(llm_client: Optional[LLMClient] = None) -> DrHypothesis:
    """Get Dr. Hypothesis agent instance."""
    return DrHypothesis(llm_client)
