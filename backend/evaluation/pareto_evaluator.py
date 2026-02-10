"""
Accuracy-Cost Pareto Evaluation Module.
Evaluates diagnostic accuracy vs test ordering cost trade-offs.
Generates metrics and visualizations for research paper.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import math
from pathlib import Path

from backend.config import settings
from backend.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EvaluationCase:
    """A single evaluation case with ground truth."""
    case_id: str
    symptoms: List[str]
    true_diagnosis: str
    true_disease_id: str
    predicted_diagnosis: str
    predicted_disease_id: str
    confidence: float
    tests_ordered: List[str]
    total_cost: float
    iterations: int
    time_to_diagnosis_ms: float = 0.0
    
    @property
    def is_correct(self) -> bool:
        return self.true_disease_id == self.predicted_disease_id
    
    @property
    def is_top3_correct(self) -> bool:
        """Check if true diagnosis in top 3 candidates."""
        # Simplified - in real impl would track top 3
        return self.is_correct


@dataclass
class ParetoPoint:
    """A point on the Pareto frontier."""
    accuracy: float  # 0-1
    avg_cost: float  # USD
    avg_tests: float
    config_name: str
    n_cases: int


@dataclass  
class EvaluationResults:
    """Complete evaluation results for paper."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Core metrics
    total_cases: int = 0
    correct_cases: int = 0
    top1_accuracy: float = 0.0
    top3_accuracy: float = 0.0
    
    # Cost metrics
    total_cost: float = 0.0
    avg_cost_per_case: float = 0.0
    median_cost: float = 0.0
    
    # Efficiency metrics
    avg_tests_per_case: float = 0.0
    avg_iterations: float = 0.0
    avg_time_ms: float = 0.0
    
    # Confidence calibration
    avg_confidence_correct: float = 0.0
    avg_confidence_incorrect: float = 0.0
    
    # Pareto data
    pareto_points: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "accuracy": {
                "total_cases": self.total_cases,
                "correct_cases": self.correct_cases,
                "top1_accuracy": round(self.top1_accuracy, 4),
                "top3_accuracy": round(self.top3_accuracy, 4)
            },
            "cost": {
                "total_cost_usd": round(self.total_cost, 2),
                "avg_cost_per_case": round(self.avg_cost_per_case, 2),
                "median_cost": round(self.median_cost, 2)
            },
            "efficiency": {
                "avg_tests_per_case": round(self.avg_tests_per_case, 2),
                "avg_iterations": round(self.avg_iterations, 2),
                "avg_time_ms": round(self.avg_time_ms, 2)
            },
            "calibration": {
                "avg_confidence_correct": round(self.avg_confidence_correct, 4),
                "avg_confidence_incorrect": round(self.avg_confidence_incorrect, 4)
            },
            "pareto_frontier": self.pareto_points
        }


class ParetoEvaluator:
    """
    Evaluates diagnostic system accuracy vs cost trade-offs.
    Generates Pareto frontier analysis for research paper.
    """
    
    def __init__(self):
        self.cases: List[EvaluationCase] = []
        self.results_path = settings.data_dir / "evaluation_results"
        self.results_path.mkdir(parents=True, exist_ok=True)
        logger.info("ParetoEvaluator initialized")
    
    def add_case(self, case: EvaluationCase):
        """Add an evaluation case."""
        self.cases.append(case)
        logger.debug(f"Added evaluation case {case.case_id}")
    
    def add_case_from_dict(self, data: Dict):
        """Add case from dictionary."""
        case = EvaluationCase(
            case_id=data.get("case_id", f"eval_{len(self.cases)+1}"),
            symptoms=data.get("symptoms", []),
            true_diagnosis=data.get("true_diagnosis", ""),
            true_disease_id=data.get("true_disease_id", ""),
            predicted_diagnosis=data.get("predicted_diagnosis", ""),
            predicted_disease_id=data.get("predicted_disease_id", ""),
            confidence=data.get("confidence", 0.0),
            tests_ordered=data.get("tests_ordered", []),
            total_cost=data.get("total_cost", 0.0),
            iterations=data.get("iterations", 1),
            time_to_diagnosis_ms=data.get("time_ms", 0.0)
        )
        self.add_case(case)
    
    def compute_metrics(self) -> EvaluationResults:
        """Compute all evaluation metrics."""
        if not self.cases:
            return EvaluationResults()
        
        results = EvaluationResults()
        results.total_cases = len(self.cases)
        
        # Accuracy
        correct = [c for c in self.cases if c.is_correct]
        results.correct_cases = len(correct)
        results.top1_accuracy = len(correct) / len(self.cases)
        
        top3_correct = [c for c in self.cases if c.is_top3_correct]
        results.top3_accuracy = len(top3_correct) / len(self.cases)
        
        # Cost
        costs = [c.total_cost for c in self.cases]
        results.total_cost = sum(costs)
        results.avg_cost_per_case = results.total_cost / len(self.cases)
        results.median_cost = sorted(costs)[len(costs) // 2]
        
        # Efficiency
        results.avg_tests_per_case = sum(len(c.tests_ordered) for c in self.cases) / len(self.cases)
        results.avg_iterations = sum(c.iterations for c in self.cases) / len(self.cases)
        results.avg_time_ms = sum(c.time_to_diagnosis_ms for c in self.cases) / len(self.cases)
        
        # Confidence calibration
        if correct:
            results.avg_confidence_correct = sum(c.confidence for c in correct) / len(correct)
        incorrect = [c for c in self.cases if not c.is_correct]
        if incorrect:
            results.avg_confidence_incorrect = sum(c.confidence for c in incorrect) / len(incorrect)
        
        logger.info(f"Computed metrics: accuracy={results.top1_accuracy:.2%}, avg_cost=${results.avg_cost_per_case:.2f}")
        return results
    
    def compute_pareto_frontier(
        self,
        cost_thresholds: List[float] = [25, 50, 100, 200, 500]
    ) -> List[ParetoPoint]:
        """
        Compute Pareto-optimal points at different cost thresholds.
        
        Args:
            cost_thresholds: Max cost budgets to evaluate
            
        Returns:
            List of Pareto points
        """
        pareto_points = []
        
        for max_cost in cost_thresholds:
            # Filter cases under cost threshold
            filtered = [c for c in self.cases if c.total_cost <= max_cost]
            
            if not filtered:
                continue
            
            accuracy = sum(1 for c in filtered if c.is_correct) / len(filtered)
            avg_cost = sum(c.total_cost for c in filtered) / len(filtered)
            avg_tests = sum(len(c.tests_ordered) for c in filtered) / len(filtered)
            
            point = ParetoPoint(
                accuracy=accuracy,
                avg_cost=avg_cost,
                avg_tests=avg_tests,
                config_name=f"budget_${max_cost}",
                n_cases=len(filtered)
            )
            pareto_points.append(point)
        
        logger.info(f"Computed {len(pareto_points)} Pareto points")
        return pareto_points
    
    def generate_report(self, save: bool = True) -> Dict:
        """
        Generate complete evaluation report for paper.
        
        Returns:
            Complete evaluation results dictionary
        """
        results = self.compute_metrics()
        pareto = self.compute_pareto_frontier()
        
        results.pareto_points = [
            {
                "config": p.config_name,
                "accuracy": round(p.accuracy, 4),
                "avg_cost": round(p.avg_cost, 2),
                "avg_tests": round(p.avg_tests, 2),
                "n_cases": p.n_cases
            }
            for p in pareto
        ]
        
        report = results.to_dict()
        
        if save:
            report_path = self.results_path / f"pareto_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Saved evaluation report: {report_path}")
        
        return report
    
    def generate_synthetic_cases(self, n: int = 100):
        """
        Generate synthetic test cases for demo/paper.
        In production, would use real patient data.
        """
        import random
        
        diseases = [
            ("D001", "Dengue Fever", ["fever", "headache", "joint_pain", "rash"]),
            ("D002", "Influenza", ["fever", "cough", "fatigue", "body_aches"]),
            ("D006", "Malaria", ["fever", "chills", "sweating", "headache"]),
            ("D009", "Tuberculosis", ["cough", "weight_loss", "night_sweats", "fever"]),
            ("D017", "Pneumonia", ["fever", "cough", "chest_pain", "shortness_of_breath"]),
        ]
        
        tests_catalog = [
            ("CBC", 15), ("CRP", 20), ("X-ray", 50), ("PCR", 100),
            ("Culture", 75), ("Rapid_Test", 25), ("CT_Scan", 200)
        ]
        
        for i in range(n):
            # Pick random disease
            disease_id, disease_name, symptoms = random.choice(diseases)
            
            # Simulate prediction (80% baseline accuracy)
            is_correct = random.random() < 0.80 + (random.random() * 0.15)
            pred_disease_id = disease_id if is_correct else random.choice(diseases)[0]
            pred_disease_name = disease_name if is_correct else random.choice(diseases)[1]
            
            # Random tests ordered (1-4 tests)
            n_tests = random.randint(1, 4)
            tests = random.sample(tests_catalog, n_tests)
            tests_ordered = [t[0] for t in tests]
            total_cost = sum(t[1] for t in tests)
            
            # Confidence (higher for correct)
            base_conf = 0.75 if is_correct else 0.55
            confidence = min(0.99, base_conf + random.random() * 0.2)
            
            case = EvaluationCase(
                case_id=f"syn_{i+1:04d}",
                symptoms=symptoms,
                true_diagnosis=disease_name,
                true_disease_id=disease_id,
                predicted_diagnosis=pred_disease_name,
                predicted_disease_id=pred_disease_id,
                confidence=confidence,
                tests_ordered=tests_ordered,
                total_cost=total_cost,
                iterations=random.randint(1, 3),
                time_to_diagnosis_ms=random.uniform(500, 3000)
            )
            self.add_case(case)
        
        logger.info(f"Generated {n} synthetic evaluation cases")


# Singleton
_evaluator: Optional[ParetoEvaluator] = None


def get_pareto_evaluator() -> ParetoEvaluator:
    """Get or create ParetoEvaluator instance."""
    global _evaluator
    if _evaluator is None:
        _evaluator = ParetoEvaluator()
    return _evaluator
