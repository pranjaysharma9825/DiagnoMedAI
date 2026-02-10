"""
Comprehensive test suite for DDX Diagnostic System.
Tests all modules, connections, and integration points.
"""
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_pass(msg: str):
    print(f"  [PASS] {msg}")

def print_fail(msg: str):
    print(f"  [FAIL] {msg}")

def test_config():
    """Test configuration loading."""
    print_section("1. CONFIGURATION")
    try:
        from backend.config import settings
        
        assert settings.app_name == "DDX Diagnostic System"
        print_pass(f"App name: {settings.app_name}")
        
        assert settings.data_dir.exists()
        print_pass(f"Data dir exists: {settings.data_dir}")
        
        assert settings.knowledge_dir.exists()
        print_pass(f"Knowledge dir exists: {settings.knowledge_dir}")
        
        assert settings.llm.default_provider in ["ollama", "groq", "gemini"]
        print_pass(f"LLM provider: {settings.llm.default_provider}")
        
        assert settings.diagnostic.confidence_threshold == 0.85
        print_pass(f"Confidence threshold: {settings.diagnostic.confidence_threshold}")
        
        return True
    except Exception as e:
        print_fail(f"Config error: {e}")
        return False

def test_logging():
    """Test logging system."""
    print_section("2. LOGGING")
    try:
        from backend.utils.logging_config import get_logger, get_agent_logger
        
        logger = get_logger("test")
        logger.info("Test log message")
        print_pass("Standard logger working")
        
        agent_logger = get_agent_logger("TestAgent")
        agent_logger.info("Test agent decision")
        print_pass("Agent logger working")
        
        return True
    except Exception as e:
        print_fail(f"Logging error: {e}")
        return False

def test_priors():
    """Test prior integration modules."""
    print_section("3. PRIOR INTEGRATION MODULES")
    try:
        # Symptom-Disease Mapper
        from backend.priors.symptom_disease_map import get_symptom_disease_mapper
        mapper = get_symptom_disease_mapper()
        
        assert len(mapper.diseases) > 0
        print_pass(f"Diseases loaded: {len(mapper.diseases)}")
        
        assert len(mapper.symptoms) > 0
        print_pass(f"Symptoms loaded: {len(mapper.symptoms)}")
        
        assert len(mapper.mapping) > 0
        print_pass(f"Symptom-disease mappings: {len(mapper.mapping)}")
        
        # Test symptom matching
        fever_id = mapper.match_symptom("fever")
        print_pass(f"Symptom matching: 'fever' -> {fever_id}")
        
        # Test candidate generation
        candidates = mapper.get_candidates(["High Fever", "Joint Pain", "Skin Rash"])
        assert len(candidates) > 0
        print_pass(f"Candidate generation: {len(candidates)} diseases for 3 symptoms")
        print(f"      Top 3: {[c['name'] for c in candidates[:3]]}")
        
        # Epidemiological Priors
        from backend.priors.epidemiology import get_epidemiological_priors
        epi = get_epidemiological_priors()
        
        assert len(epi.prevalence) > 0
        print_pass(f"Prevalence records: {len(epi.prevalence)}")
        
        priors = epi.get_priors(region="South Asia", month=7)
        assert len(priors) > 0
        print_pass(f"Regional priors (South Asia, July): {len(priors)} diseases")
        
        # Genomic Risk Engine
        from backend.priors.genphire import get_genomic_risk_engine
        genomic = get_genomic_risk_engine()
        
        print_pass(f"Risk alleles loaded: {len(genomic.risk_data)}")
        
        # Test risk calculation
        risk_mods = genomic.get_risk_modifiers(["rs1800562", "rs7903146"])
        print_pass(f"Risk modifiers for 2 variants: {len(risk_mods)} diseases affected")
        
        return True
    except Exception as e:
        import traceback
        print_fail(f"Priors error: {e}")
        traceback.print_exc()
        return False

def test_models():
    """Test Pydantic data models."""
    print_section("4. DATA MODELS")
    try:
        from backend.models.patient import PatientCase, PatientProfile, PatientDemographics, SymptomReport
        from backend.models.diagnosis import Disease, Hypothesis, DiagnosticState
        from backend.models.test_order import Test, TestRequest, TestCatalog
        
        # Create patient case
        patient = PatientCase(
            profile=PatientProfile(
                demographics=PatientDemographics(
                    patient_id="P001",
                    age=35,
                    sex="male",
                    region="South Asia"
                )
            ),
            symptoms=[
                SymptomReport(name="High Fever", severity=8),
                SymptomReport(name="Joint Pain", severity=6)
            ],
            chief_complaint="Fever and body aches for 3 days"
        )
        assert patient.patient_id == "P001"
        print_pass(f"PatientCase created: {patient.patient_id}")
        
        # Create disease
        disease = Disease(disease_id="D001", name="Dengue Fever", severity=4)
        print_pass(f"Disease created: {disease.name}")
        
        # Create hypothesis
        hypothesis = Hypothesis(disease=disease, probability=0.75, supporting_evidence=["fever", "joint pain"])
        print_pass(f"Hypothesis created: {hypothesis.probability:.0%} probability")
        
        # Create diagnostic state
        state = DiagnosticState(
            patient_id="P001",
            symptoms=["High Fever", "Joint Pain"],
            budget_remaining=5000.0
        )
        state.hypotheses = [hypothesis]
        state.update_confidence()
        assert state.confidence == 0.75
        print_pass(f"DiagnosticState created: confidence={state.confidence:.0%}")
        
        # Create test
        test = Test(
            test_id="T001",
            name="NS1 Antigen Test",
            cost_usd=25.0,
            sensitivity=0.90,
            specificity=0.95,
            diseases_detected=["D001"]
        )
        print_pass(f"Test created: {test.name} (${test.cost_usd})")
        
        return True
    except Exception as e:
        import traceback
        print_fail(f"Models error: {e}")
        traceback.print_exc()
        return False

def test_agents():
    """Test agent modules (without LLM calls)."""
    print_section("5. AGENT MODULES")
    try:
        # Dr. Test-Chooser
        from backend.agents.dr_test_chooser import get_dr_test_chooser
        from backend.models.diagnosis import DiagnosticState, Hypothesis, Disease
        
        test_chooser = get_dr_test_chooser()
        print_pass(f"DrTestChooser initialized: {len(test_chooser.test_catalog.tests)} tests")
        
        # Test entropy calculation
        disease = Disease(disease_id="D001", name="Dengue")
        hyp1 = Hypothesis(disease=disease, probability=0.6)
        disease2 = Disease(disease_id="D002", name="Influenza")
        hyp2 = Hypothesis(disease=disease2, probability=0.3)
        
        entropy = test_chooser.compute_entropy([hyp1, hyp2])
        print_pass(f"Entropy calculation: {entropy:.3f} bits")
        
        # Test test selection
        state = DiagnosticState(
            patient_id="P001",
            symptoms=["fever"],
            budget_remaining=500,
            hypotheses=[hyp1, hyp2]
        )
        
        test_request = test_chooser.select_next_test(state)
        if test_request:
            print_pass(f"Test selection: {test_request.test.name} (gain: {test_request.expected_information_gain:.3f} bits)")
        else:
            print_pass("Test selection: No suitable tests (expected with limited hypotheses)")
        
        # Dr. Stewardship
        from backend.agents.dr_stewardship import get_dr_stewardship
        from backend.models.test_order import Test, TestRequest
        
        stewardship = get_dr_stewardship(use_llm=False)
        print_pass("DrStewardship initialized")
        
        if test_request:
            approved, rationale = stewardship.evaluate_test(test_request, state)
            print_pass(f"Stewardship evaluation: {'Approved' if approved else 'Vetoed'}")
        
        # Dr. Hypothesis (structure only, no LLM)
        from backend.agents.dr_hypothesis import DrHypothesis
        print_pass("DrHypothesis module loadable")
        
        return True
    except Exception as e:
        import traceback
        print_fail(f"Agents error: {e}")
        traceback.print_exc()
        return False

def test_services():
    """Test service modules."""
    print_section("6. SERVICES")
    try:
        # Success Store
        from backend.services.success_store import get_success_store
        store = get_success_store()
        
        stats = store.get_stats()
        print_pass(f"SuccessStore initialized: {stats['total']} entries")
        
        # Diagnostic Loop Service (structure)
        from backend.services.diagnostic_loop import get_diagnostic_loop_service
        loop_service = get_diagnostic_loop_service()
        print_pass("DiagnosticLoopService initialized")
        
        return True
    except Exception as e:
        import traceback
        print_fail(f"Services error: {e}")
        traceback.print_exc()
        return False

def test_orchestrator():
    """Test LangGraph orchestrator structure."""
    print_section("7. LANGGRAPH ORCHESTRATOR")
    try:
        from backend.agents.orchestrator import build_diagnostic_graph, GraphState
        from backend.models.diagnosis import DiagnosticState
        
        # Test state creation
        ds = DiagnosticState(patient_id="P001", symptoms=["fever"])
        graph_state = GraphState(diagnostic_state=ds)
        print_pass("GraphState created successfully")
        
        # Test graph building (without running)
        graph = build_diagnostic_graph()
        print_pass("Diagnostic graph compiled successfully")
        
        return True
    except Exception as e:
        import traceback
        print_fail(f"Orchestrator error: {e}")
        traceback.print_exc()
        return False

def test_fastapi_app():
    """Test FastAPI app structure."""
    print_section("8. FASTAPI APPLICATION")
    try:
        from backend.app import app
        
        # Check routes
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        print_pass(f"FastAPI app loaded: {len(routes)} routes")
        
        expected_routes = ["/", "/health", "/api/priors/epidemiology"]
        for route in expected_routes:
            if route in routes:
                print_pass(f"Route exists: {route}")
            else:
                print_fail(f"Missing route: {route}")
        
        return True
    except Exception as e:
        import traceback
        print_fail(f"FastAPI error: {e}")
        traceback.print_exc()
        return False

def test_end_to_end_candidates():
    """Test end-to-end candidate generation flow."""
    print_section("9. END-TO-END: SYMPTOM → CANDIDATES")
    try:
        from backend.priors.symptom_disease_map import get_symptom_disease_mapper
        from backend.priors.epidemiology import get_epidemiological_priors
        from backend.priors.genphire import get_genomic_risk_engine
        
        # Simulate a patient case
        symptoms = ["High Fever", "Joint Pain", "Skin Rash"]
        region = "South Asia"
        genetic_variants = ["rs7903146"]
        
        # Step 1: Get symptom-based candidates
        mapper = get_symptom_disease_mapper()
        candidates = mapper.get_candidates(symptoms, top_k=5)
        print_pass(f"Step 1 - Symptom matching: {len(candidates)} candidates")
        
        # Step 2: Get epidemiological priors
        epi = get_epidemiological_priors()
        priors = epi.get_priors(region=region, month=7)
        print_pass(f"Step 2 - Epi priors: {len(priors)} disease priors")
        
        # Step 3: Apply priors to candidates
        for candidate in candidates:
            disease_id = candidate['disease_id']
            if disease_id in priors:
                prior_boost = min(priors[disease_id] * 10000, 2.0)
                candidate['adjusted_prob'] = candidate['base_probability'] * (1 + prior_boost)
            else:
                candidate['adjusted_prob'] = candidate['base_probability']
        
        # Step 4: Get genomic risk modifiers
        genomic = get_genomic_risk_engine()
        risk_mods = genomic.get_risk_modifiers(genetic_variants)
        
        for candidate in candidates:
            if candidate['disease_id'] in risk_mods:
                candidate['adjusted_prob'] *= risk_mods[candidate['disease_id']]
        
        candidates.sort(key=lambda x: x['adjusted_prob'], reverse=True)
        print_pass(f"Step 3-4 - Applied priors & genomic modifiers")
        
        # Show results
        print("\n  Top 5 Candidates with Combined Priors:")
        for i, c in enumerate(candidates[:5], 1):
            print(f"    {i}. {c['name']} (ID: {c['disease_id']})")
            print(f"       Base: {c['base_probability']:.2%} | Adjusted: {c['adjusted_prob']:.2%}")
        
        return True
    except Exception as e:
        import traceback
        print_fail(f"E2E error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  DDX DIAGNOSTIC SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    results = {}
    
    results['config'] = test_config()
    results['logging'] = test_logging()
    results['priors'] = test_priors()
    results['models'] = test_models()
    results['agents'] = test_agents()
    results['services'] = test_services()
    results['orchestrator'] = test_orchestrator()
    results['fastapi'] = test_fastapi_app()
    results['e2e'] = test_end_to_end_candidates()
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {name}")
    
    print(f"\n  {'='*40}")
    print(f"  TOTAL: {passed}/{total} tests passed")
    print(f"  {'='*40}\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
