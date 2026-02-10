"""
LangGraph-based orchestrator for the multi-agent diagnostic workflow.
Coordinates Dr. Hypothesis, Dr. Test-Chooser, and Dr. Stewardship.
"""
from typing import Dict, Any, Optional, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from backend.models.diagnosis import DiagnosticState, Hypothesis, DiagnosisResult
from backend.models.test_order import TestRequest
from backend.agents.dr_hypothesis import DrHypothesis, get_dr_hypothesis
from backend.agents.dr_test_chooser import DrTestChooser, get_dr_test_chooser
from backend.agents.dr_stewardship import DrStewardship, get_dr_stewardship
from backend.priors.epidemiology import get_epidemiological_priors
from backend.priors.genphire import get_genomic_risk_engine
from backend.priors.symptom_disease_map import get_symptom_disease_mapper
from backend.config import settings
from backend.utils.logging_config import get_logger, get_agent_logger

logger = get_logger(__name__)
orchestrator_logger = get_agent_logger("Orchestrator")


class GraphState(BaseModel):
    """State passed through the LangGraph workflow."""
    # Core diagnostic state
    diagnostic_state: DiagnosticState
    
    # Workflow control
    current_test_request: Optional[TestRequest] = None
    awaiting_test_result: bool = False
    test_approved: bool = False
    veto_reason: Optional[str] = None
    
    # Completion flags
    diagnosis_complete: bool = False
    max_iterations_reached: bool = False
    
    class Config:
        arbitrary_types_allowed = True


def should_continue(state: GraphState) -> Literal["test_chooser", "finalize"]:
    """Decide whether to continue testing or finalize diagnosis."""
    ds = state.diagnostic_state
    
    # Check confidence threshold
    if ds.confidence >= settings.diagnostic.confidence_threshold:
        orchestrator_logger.info(f"Confidence {ds.confidence:.1%} >= threshold, finalizing")
        return "finalize"
    
    # Check iteration limit
    if ds.iteration >= settings.diagnostic.max_iterations:
        orchestrator_logger.info(f"Max iterations ({ds.iteration}) reached, finalizing")
        return "finalize"
    
    # Check budget
    if ds.budget_remaining <= 0:
        orchestrator_logger.info("Budget exhausted, finalizing")
        return "finalize"
    
    return "test_chooser"


def should_await_or_loop(state: GraphState) -> Literal["await_results", "hypothesis", "end"]:
    """Decide next step after stewardship review."""
    if state.awaiting_test_result:
        return "await_results"
    
    if state.test_approved:
        return "await_results"
    
    if state.diagnosis_complete:
        return "end"
    
    # Test was vetoed, try another
    return "hypothesis"


async def hypothesis_node(state: GraphState) -> GraphState:
    """Dr. Hypothesis generates/updates the differential diagnosis."""
    orchestrator_logger.info(f"=== HYPOTHESIS NODE (iter {state.diagnostic_state.iteration + 1}) ===")
    
    ds = state.diagnostic_state
    dr_hypothesis = get_dr_hypothesis()
    
    if ds.iteration == 0:
        # Initial DDx
        hypotheses = await dr_hypothesis.generate_initial_ddx(
            symptoms=ds.symptoms,
            region="Global"
        )
    else:
        # Update with new evidence
        hypotheses = await dr_hypothesis.update_ddx(
            state=ds,
            new_test_result=ds.test_results
        )
    
    # Update state
    ds.hypotheses = hypotheses
    ds.update_confidence()
    ds.iteration += 1
    ds.updated_at = datetime.now()
    
    orchestrator_logger.info(
        f"DDx updated: {len(hypotheses)} hypotheses, "
        f"top: {hypotheses[0].disease.name if hypotheses else 'None'} "
        f"({hypotheses[0].probability:.1%} if hypotheses else 0)" if hypotheses else "(no hypotheses)"
    )
    
    return GraphState(
        diagnostic_state=ds,
        awaiting_test_result=False,
        test_approved=False
    )


async def test_chooser_node(state: GraphState) -> GraphState:
    """Dr. Test-Chooser selects the next optimal test."""
    orchestrator_logger.info("=== TEST CHOOSER NODE ===")
    
    ds = state.diagnostic_state
    dr_test_chooser = get_dr_test_chooser()
    
    test_request = dr_test_chooser.select_next_test(state=ds)
    
    if test_request is None:
        orchestrator_logger.info("No suitable tests available")
        return GraphState(
            diagnostic_state=ds,
            current_test_request=None,
            diagnosis_complete=True
        )
    
    orchestrator_logger.info(f"Proposed: {test_request.test.name} (${test_request.test.cost_usd})")
    
    return GraphState(
        diagnostic_state=ds,
        current_test_request=test_request,
        awaiting_test_result=False,
        test_approved=False
    )


async def stewardship_node(state: GraphState) -> GraphState:
    """Dr. Stewardship evaluates the proposed test."""
    orchestrator_logger.info("=== STEWARDSHIP NODE ===")
    
    ds = state.diagnostic_state
    dr_stewardship = get_dr_stewardship()
    
    if state.current_test_request is None:
        return GraphState(
            diagnostic_state=ds,
            test_approved=False,
            diagnosis_complete=True
        )
    
    approved, rationale = dr_stewardship.evaluate_test(
        test_request=state.current_test_request,
        state=ds
    )
    
    if approved:
        orchestrator_logger.info(f"APPROVED: {state.current_test_request.test.name}")
        # Deduct cost
        ds.budget_remaining -= state.current_test_request.test.cost_usd
        ds.total_cost += state.current_test_request.test.cost_usd
        ds.pending_tests.append(state.current_test_request.test.test_id)
    else:
        orchestrator_logger.info(f"VETOED: {rationale}")
    
    return GraphState(
        diagnostic_state=ds,
        current_test_request=state.current_test_request if approved else None,
        awaiting_test_result=approved,
        test_approved=approved,
        veto_reason=None if approved else rationale
    )


async def finalize_node(state: GraphState) -> GraphState:
    """Finalize the diagnosis."""
    orchestrator_logger.info("=== FINALIZE NODE ===")
    
    ds = state.diagnostic_state
    
    return GraphState(
        diagnostic_state=ds,
        diagnosis_complete=True
    )


def build_diagnostic_graph() -> StateGraph:
    """Build the LangGraph workflow for diagnostic reasoning."""
    
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("hypothesis", hypothesis_node)
    workflow.add_node("test_chooser", test_chooser_node)
    workflow.add_node("stewardship", stewardship_node)
    workflow.add_node("finalize", finalize_node)
    
    # Set entry point
    workflow.set_entry_point("hypothesis")
    
    # Add edges
    workflow.add_conditional_edges(
        "hypothesis",
        should_continue,
        {
            "test_chooser": "test_chooser",
            "finalize": "finalize"
        }
    )
    
    workflow.add_edge("test_chooser", "stewardship")
    
    workflow.add_conditional_edges(
        "stewardship",
        should_await_or_loop,
        {
            "await_results": END,  # Exit to await user input
            "hypothesis": "hypothesis",  # Test vetoed, try again
            "end": "finalize"
        }
    )
    
    workflow.add_edge("finalize", END)
    
    return workflow.compile()


# Compiled graph instance
_diagnostic_graph = None


def get_diagnostic_graph() -> StateGraph:
    """Get or create the diagnostic graph."""
    global _diagnostic_graph
    if _diagnostic_graph is None:
        _diagnostic_graph = build_diagnostic_graph()
    return _diagnostic_graph
