"""
Diagnostic loop service - main workflow controller.
Manages the iterative diagnostic process with user interaction.
"""
from typing import AsyncGenerator, Optional, Dict
from datetime import datetime
import uuid

from backend.models.patient import PatientCase
from backend.models.diagnosis import DiagnosticState, DiagnosisResult
from backend.models.test_order import TestRequest, TestResult
from backend.agents.orchestrator import (
    GraphState, 
    get_diagnostic_graph,
    build_diagnostic_graph
)
from backend.priors.epidemiology import get_epidemiological_priors
from backend.priors.genphire import get_genomic_risk_engine
from backend.priors.symptom_disease_map import get_symptom_disease_mapper
from backend.config import settings
from backend.utils.logging_config import get_logger, get_agent_logger

logger = get_logger(__name__)
loop_logger = get_agent_logger("DiagnosticLoop")


class DiagnosticSession:
    """Manages a single diagnostic session for a patient."""
    
    def __init__(self, session_id: str, patient_case: PatientCase):
        self.session_id = session_id
        self.patient_case = patient_case
        self.state: Optional[GraphState] = None
        self.history: list = []
        self.created_at = datetime.now()
        self.status = "initialized"
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "patient_id": self.patient_case.patient_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "iterations": self.state.diagnostic_state.iteration if self.state else 0,
            "confidence": self.state.diagnostic_state.confidence if self.state else 0,
            "budget_remaining": self.state.diagnostic_state.budget_remaining if self.state else 0
        }


class DiagnosticLoopService:
    """
    Service managing the diagnostic loop.
    Handles session management and workflow coordination.
    """
    
    def __init__(self):
        self.sessions: Dict[str, DiagnosticSession] = {}
        self.graph = None
        logger.info("DiagnosticLoopService initialized")
    
    def _get_graph(self):
        """Lazy-load the diagnostic graph."""
        if self.graph is None:
            self.graph = build_diagnostic_graph()
        return self.graph
    
    async def start_diagnosis(
        self,
        patient_case: PatientCase
    ) -> tuple[str, DiagnosticState]:
        """
        Start a new diagnostic session.
        
        Args:
            patient_case: Complete patient case with symptoms
            
        Returns:
            Tuple of (session_id, initial diagnostic state)
        """
        session_id = str(uuid.uuid4())[:8]
        loop_logger.info(f"Starting diagnosis session {session_id}")
        
        # Initialize diagnostic state
        symptom_names = [s.name for s in patient_case.symptoms]
        symptom_mapper = get_symptom_disease_mapper()
        symptom_ids = []
        for name in symptom_names:
            sid = symptom_mapper.match_symptom(name)
            if sid:
                symptom_ids.append(sid)
        
        # Get priors
        epi_priors = get_epidemiological_priors()
        priors = epi_priors.get_priors(region=patient_case.profile.region)
        
        # Apply genomic modifiers
        if patient_case.profile.genetic_variants:
            genomic_engine = get_genomic_risk_engine()
            variant_ids = [v.rsid for v in patient_case.profile.genetic_variants]
            risk_mods = genomic_engine.get_risk_modifiers(variant_ids)
            for disease_id, modifier in risk_mods.items():
                if disease_id in priors:
                    priors[disease_id] *= modifier
        
        # Create diagnostic state
        diagnostic_state = DiagnosticState(
            patient_id=patient_case.patient_id,
            symptoms=symptom_names,
            symptom_ids=symptom_ids,
            priors=priors,
            budget_remaining=settings.diagnostic.default_budget_usd,
            started_at=datetime.now()
        )
        
        # Create session
        session = DiagnosticSession(session_id, patient_case)
        session.state = GraphState(diagnostic_state=diagnostic_state)
        session.status = "started"
        self.sessions[session_id] = session
        
        loop_logger.info(
            f"Session {session_id} created: "
            f"{len(symptom_names)} symptoms, {len(priors)} priors"
        )
        
        return session_id, diagnostic_state
    
    async def run_iteration(
        self,
        session_id: str
    ) -> tuple[GraphState, Optional[TestRequest]]:
        """
        Run one iteration of the diagnostic loop.
        
        Args:
            session_id: The session to advance
            
        Returns:
            Tuple of (updated state, pending test request if any)
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        loop_logger.info(f"Running iteration for session {session_id}")
        
        graph = self._get_graph()
        
        # Run graph until it needs user input or completes
        result = await graph.ainvoke(session.state)
        
        session.state = result
        session.history.append({
            "iteration": result.diagnostic_state.iteration,
            "confidence": result.diagnostic_state.confidence,
            "timestamp": datetime.now().isoformat()
        })
        
        if result.diagnosis_complete:
            session.status = "complete"
            loop_logger.info(f"Session {session_id} complete")
        elif result.awaiting_test_result:
            session.status = "awaiting_test"
            loop_logger.info(f"Session {session_id} awaiting test result")
        
        return result, result.current_test_request
    
    async def submit_test_result(
        self,
        session_id: str,
        test_id: str,
        result: str
    ) -> GraphState:
        """
        Submit a test result and continue the diagnostic loop.
        
        Args:
            session_id: The session to update
            test_id: ID of the completed test
            result: Test result (e.g., "positive", "negative", value)
            
        Returns:
            Updated graph state
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        loop_logger.info(f"Test result for session {session_id}: {test_id} = {result}")
        
        ds = session.state.diagnostic_state
        
        # Update state with result
        ds.test_results[test_id] = result
        if test_id in ds.pending_tests:
            ds.pending_tests.remove(test_id)
        ds.completed_tests.append(test_id)
        
        # Update session state
        session.state = GraphState(
            diagnostic_state=ds,
            awaiting_test_result=False,
            test_approved=False
        )
        session.status = "running"
        
        return session.state
    
    def get_session(self, session_id: str) -> Optional[DiagnosticSession]:
        """Get a diagnostic session."""
        return self.sessions.get(session_id)
    
    def get_result(self, session_id: str) -> Optional[DiagnosisResult]:
        """
        Get the final diagnosis result for a completed session.
        """
        session = self.sessions.get(session_id)
        if not session or session.status != "complete":
            return None
        
        ds = session.state.diagnostic_state
        top = ds.top_hypothesis
        
        if not top:
            return None
        
        return DiagnosisResult(
            patient_id=ds.patient_id,
            final_diagnosis=top.disease,
            confidence=ds.confidence,
            differential=ds.hypotheses,
            tests_ordered=ds.completed_tests,
            total_cost=ds.total_cost,
            iterations=ds.iteration,
            reasoning_trace=[f"Iteration {i+1}" for i in range(ds.iteration)]
        )


# Singleton service instance
_service_instance: Optional[DiagnosticLoopService] = None


def get_diagnostic_loop_service() -> DiagnosticLoopService:
    """Get or create the diagnostic loop service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = DiagnosticLoopService()
    return _service_instance
