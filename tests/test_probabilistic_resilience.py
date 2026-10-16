"""
PRUBETH IDE — Mathematical Verification of Probabilistic Resilience
===================================================================
Tests formal mathematical reliability functions, Weibull distributions,
PRINCE2 FMEA RPN scoring, missing drive path self-healing, handle expansions,
and Kahn's DAG cycle-breaking algorithms.
"""

import math
import os
import tempfile
from pathlib import Path
import pytest

from core.probabilistic_resilience_engine import (
    ProbabilisticResilienceEngine, FailureModeRisk, ProbabilisticReliabilityMetrics,
    EventStormTokenBucket, CryptographicBloomFilter, ResilientCircuitBreaker,
    CircuitState, CircuitBreakerOpenError
)
from core.reliability_engine import ReliabilityEngine, ReliabilityProfile, StageGateDecision


def test_weibull_and_series_probability_math():
    engine = ProbabilisticResilienceEngine.get_instance()

    # 1. Zero hours has 100% survival
    assert engine.calculate_weibull_survival(0.0) == 1.0

    # 2. Survival monotonically decays over time under wear-out beta = 1.25
    r_10h = engine.calculate_weibull_survival(10.0, beta=1.25, eta=500.0)
    r_100h = engine.calculate_weibull_survival(100.0, beta=1.25, eta=500.0)
    r_500h = engine.calculate_weibull_survival(500.0, beta=1.25, eta=500.0)

    assert 0.0 < r_500h < r_100h < r_10h < 1.0
    # At t = eta, Weibull survival R(eta) = exp(-1) = 0.367879...
    assert math.isclose(r_500h, math.exp(-1.0), rel_tol=1e-4)

    # 3. Series failure probability without transactional rollback
    # P(fail) for 100 steps with 0.1% individual step risk
    p_fail_100 = engine.calculate_series_failure_probability(100, 0.001)
    expected_survival = (1.0 - 0.001) ** 100
    assert math.isclose(p_fail_100, 1.0 - expected_survival, rel_tol=1e-4)
    assert p_fail_100 > 0.09  # ~9.5% unreliability without transaction guard


def test_shannon_entropy_calculation():
    engine = ProbabilisticResilienceEngine.get_instance()

    # Uniform random distribution has higher entropy than repetitive text
    low_entropy = engine.calculate_shannon_entropy("AAAAAAAAAAAA")
    high_entropy = engine.calculate_shannon_entropy("The quick brown fox jumps over the lazy dog 1234567890!")

    assert low_entropy == 0.0
    assert high_entropy > 4.0


def test_prince2_fmea_risk_matrix():
    engine = ProbabilisticResilienceEngine.get_instance()
    risks = engine.evaluate_fmea_risks()

    assert len(risks) >= 6
    for r in risks:
        assert 1 <= r.severity <= 10
        assert 1 <= r.occurrence <= 10
        assert 1 <= r.detection <= 10
        assert r.rpn == r.severity * r.occurrence * r.detection
        assert r.mitigation_active is True

    # Memory OOM should have high severity
    oom_risk = [r for r in risks if "Memory" in r.name][0]
    assert oom_risk.severity == 10


def test_missing_drive_path_self_healing(tmp_path):
    engine = ProbabilisticResilienceEngine(workspace_root=tmp_path)

    # Create dummy app file in workspace
    dummy_exe = tmp_path / "VSCode-win32-x64" / "PRUBETH.exe"
    dummy_exe.parent.mkdir(parents=True, exist_ok=True)
    dummy_exe.write_text("dummy binary", encoding="utf-8")

    # Simulate non-existent drive Z:\ path
    broken_z_path = r"Z:\PRUBETH IDE\PRUBETH.exe"
    healed = engine.heal_missing_drive_path(broken_z_path)

    assert healed is not None
    assert healed.exists()
    assert healed == dummy_exe.resolve()


def test_kahn_dag_cycle_detection_and_precautionary_breaker():
    engine = ProbabilisticResilienceEngine.get_instance()

    # Valid acyclic DAG: A -> B -> C, A -> D
    nodes = ["A", "B", "C", "D"]
    acyclic_edges = [("A", "B"), ("B", "C"), ("A", "D")]
    is_ok, order = engine.verify_dag_acyclic(nodes, acyclic_edges)
    assert is_ok is True
    assert order.index("A") < order.index("B") < order.index("C")

    # Deadlocked cyclic DAG: A -> B -> C -> A (Infinite loop)
    cyclic_edges = [("A", "B"), ("B", "C"), ("C", "A"), ("C", "D")]
    is_cyclic, cyclic_nodes = engine.verify_dag_acyclic(nodes, cyclic_edges)
    assert is_cyclic is False
    assert {"A", "B", "C"}.issubset(set(cyclic_nodes))

    # Precautionary cycle breaker safely removes the circular loop
    healed_edges = engine.break_dag_cycles_precautionary(nodes, cyclic_edges)
    is_healed, healed_order = engine.verify_dag_acyclic(nodes, healed_edges)
    assert is_healed is True
    assert len(healed_order) == 4


def test_large_project_reliability_profile(tmp_path):
    engine = ReliabilityEngine(workspace_root=tmp_path)
    report = engine.run_profile(ReliabilityProfile.LARGE_PROJECT)

    assert report.stage_gate_decision == StageGateDecision.APPROVED
    assert report.failed_count == 0
    assert report.total_scenarios == 6

    # Verify our new scenarios ran and passed
    scenario_names = [s.name for s in report.scenarios]
    assert any("Path Invariance" in s for s in scenario_names)
    assert any("DAG Deadlock" in s for s in scenario_names)
    assert any("Handle Expansion" in s for s in scenario_names)


def test_full_jitter_exponential_backoff():
    engine = ProbabilisticResilienceEngine.get_instance()
    delays = [engine.calculate_full_jitter_backoff(attempt=3, base_delay=0.01, max_delay=0.20) for _ in range(20)]
    assert len(delays) == 20
    for d in delays:
        assert 0.001 <= d <= 0.20
    # Statistical check: values must vary (zero deterministic lock-step collisions)
    assert len(set(delays)) > 15


def test_littles_law_and_queue_saturation():
    engine = ProbabilisticResilienceEngine.get_instance()

    # Normal load: lambda = 10, mu = 20 -> rho = 0.50
    m_normal = engine.calculate_littles_law_latency(arrival_rate=10.0, service_rate=20.0)
    assert m_normal["utilization"] == 0.50
    assert m_normal["backpressure_required"] is False
    assert m_normal["latency_seconds"] == 0.10  # 1 / (20 - 10) = 0.1s

    # Saturated load: lambda = 19, mu = 20 -> rho = 0.95 -> backpressure triggered!
    m_saturated = engine.calculate_littles_law_latency(arrival_rate=19.0, service_rate=20.0)
    assert m_saturated["utilization"] == 0.95
    assert m_saturated["backpressure_required"] is True
    assert m_saturated["latency_seconds"] == 1.0  # 1 / (20 - 19) = 1.0s


def test_merkle_tree_cryptographic_integrity():
    engine = ProbabilisticResilienceEngine.get_instance()

    hashes_a = [
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "ca978112ca1bbdcafac231b39a23dc4da786081496e684db94aec6fde8b1464f",
        "fb8e20fc2e4c3f248c60c39bd652f3c1347298ab97b8b974d2ab65820260195c"
    ]
    root_a = engine.compute_merkle_tree_root(hashes_a)
    assert len(root_a) == 64

    # Identical hashes yield identical Merkle root
    assert engine.compute_merkle_tree_root(list(hashes_a)) == root_a

    # Any single-bit alteration in any file strictly changes root hash (avalanche effect)
    hashes_b = list(hashes_a)
    hashes_b[1] = "ca978112ca1bbdcafac231b39a23dc4da786081496e684db94aec6fde8b1464e"  # modified last char
    root_b = engine.compute_merkle_tree_root(hashes_b)
    assert root_a != root_b


def test_zipf_hotspot_distribution_and_gini():
    engine = ProbabilisticResilienceEngine.get_instance()

    # Highly skewed mutation distribution (20% files have 80% edits)
    mutations = {
        "core/app.py": 500,
        "core/router.py": 350,
        "ui/main.py": 200,
        "util/helper1.py": 10,
        "util/helper2.py": 8,
        "util/helper3.py": 5,
        "util/helper4.py": 4,
        "util/helper5.py": 3,
        "util/helper6.py": 2,
        "util/helper7.py": 1,
    }
    res = engine.calculate_zipf_hotspot_distribution(mutations)
    assert res["total_files"] == 10
    assert res["total_mutations"] == 1083
    assert "core/app.py" in res["top_decile_hotspots"]
    assert res["gini_coefficient"] > 0.60  # High inequality indicative of Pareto distribution


def test_poisson_collision_probability():
    engine = ProbabilisticResilienceEngine.get_instance()

    # Zero time window = zero collision
    assert engine.calculate_poisson_collision_probability(arrival_rate=10.0, delta_t=0.0) == 0.0

    # Low arrival rate in tiny delta window: very small collision probability
    p_low = engine.calculate_poisson_collision_probability(arrival_rate=1.0, delta_t=0.001)
    assert 0.0 <= p_low <= 0.0001

    # High arrival rate in larger window: significant collision probability
    p_high = engine.calculate_poisson_collision_probability(arrival_rate=50.0, delta_t=0.1)
    assert p_high > 0.50


def test_cosine_drift_calculation():
    engine = ProbabilisticResilienceEngine.get_instance()

    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    vec3 = [0.0, 1.0, 0.0]

    # Identical vectors: distance = 0.0
    assert engine.calculate_cosine_drift(vec1, vec2) == 0.0

    # Orthogonal vectors: distance = 1.0
    assert engine.calculate_cosine_drift(vec1, vec3) == 1.0


def test_knapsack_token_budget_optimization():
    engine = ProbabilisticResilienceEngine.get_instance()

    docs = [
        {"id": "doc1", "content": "Critical core architecture rules\n" * 10, "tokens": 100, "recency_sec": 10.0, "similarity": 0.95, "priority": 10},
        {"id": "doc2", "content": "Recent active editor buffer\n" * 5, "tokens": 50, "recency_sec": 5.0, "similarity": 0.90, "priority": 8},
        {"id": "doc3", "content": "Old secondary utility file\n" * 20, "tokens": 200, "recency_sec": 5000.0, "similarity": 0.40, "priority": 3},
        {"id": "doc4", "content": "Boundary candidate module\n" * 15, "tokens": 150, "recency_sec": 200.0, "similarity": 0.70, "priority": 6},
    ]

    # Capacity of 200 tokens
    res = engine.optimize_token_budget_knapsack(docs, token_capacity=200, allow_fractional_boundary=True)

    assert res["total_tokens"] <= 200
    assert res["utilization_pct"] > 80.0
    packed_ids = [d["id"] for d in res["packed_documents"]]
    # High priority & high similarity documents MUST be packed first
    assert "doc1" in packed_ids
    assert "doc2" in packed_ids
    # Low priority old doc should be discarded or sliced
    assert "doc3" not in packed_ids or packed_ids.index("doc1") < packed_ids.index("doc3")


def test_ast_static_complexity_guard_and_mccabe():
    engine = ProbabilisticResilienceEngine.get_instance()

    # 1. Clean valid Python code
    valid_code = """
def process_data(items):
    results = []
    for x in items:
        if x > 0:
            results.append(x * 2)
    return results
"""
    val_res = engine.validate_code_ast_precautionary(valid_code)
    assert val_res["is_valid"] is True
    assert val_res["cyclomatic_complexity"] == 3  # base 1 + for 1 + if 1 = 3
    assert val_res["defect_hazard"] < 0.20

    # 2. Syntax error injection
    corrupt_code = "def broken_syntax(x\n    return x + 1"
    err_res = engine.validate_code_ast_precautionary(corrupt_code)
    assert err_res["is_valid"] is False
    assert err_res["error_type"] == "SyntaxError"
    assert err_res["defect_hazard"] == 1.0

    # 3. High cyclomatic complexity exceeding limit
    hyper_complex = "def hyper():\n" + "\n".join(f"    if x == {i}: pass" for i in range(60))
    comp_res = engine.validate_code_ast_precautionary(hyper_complex, max_cyclomatic_complexity=50)
    assert comp_res["is_valid"] is False
    assert comp_res["complexity_exceeded"] is True
    assert comp_res["cyclomatic_complexity"] > 50


def test_event_storm_token_bucket_coalescence():
    tb = EventStormTokenBucket(capacity=50, refill_rate=20.0, coalescence_window_sec=0.01)

    # Ingest 100 rapid events on only 3 distinct paths
    for i in range(100):
        path = f"file_{i % 3}.py"
        tb.ingest_event(path, event_type="modified")

    import time
    time.sleep(0.02)  # Allow coalescence window to close

    flushed = tb.flush_coalesced_events()
    # 100 events coalesced to at most 3 paths
    assert len(flushed) <= 3
    reduction = tb.get_reduction_ratio()
    assert reduction >= 0.90  # >= 90% reduction in Qt event queue load


def test_universal_scalability_law_concurrency_governor():
    engine = ProbabilisticResilienceEngine.get_instance()

    # Alpha (contention) = 5%, Beta (coherency) = 0.5%
    usl = engine.calculate_optimal_concurrency_usl(
        contention_alpha=0.05,
        coherency_beta=0.005,
        gamma_scale=1.0,
        max_tested_workers=32
    )

    assert "optimal_workers_unbounded" in usl
    n_star = usl["optimal_workers_unbounded"]
    # sqrt((1 - 0.05) / 0.005) = sqrt(190) ≈ 13.78
    assert 12.0 <= n_star <= 15.0
    assert 1 <= usl["recommended_worker_pool_size"] <= 32
    assert usl["peak_relative_throughput"] > 1.0


def test_cryptographic_bloom_filter_zero_disk():
    # 1000 items with 1% target false positive rate
    bloom = CryptographicBloomFilter(expected_elements=1000, false_positive_rate=0.01)

    items = [f"src/module_{i}.py" for i in range(500)]
    for it in items:
        bloom.add(it)

    # Invariant: 100% True Positive for added items
    for it in items:
        assert bloom.contains(it) is True

    # Invariant: Absent items must return False with ~99% accuracy
    absent = [f"nonexistent_file_{j}.py" for j in range(200)]
    negatives = sum(1 for it in absent if not bloom.contains(it))
    assert negatives >= 195  # >= 97.5% true negative rate

    est_fp = bloom.estimate_current_false_positive_rate()
    assert est_fp < 0.05


def test_resilient_circuit_breaker_markov_state_transitions():
    cb = ResilientCircuitBreaker(
        failure_threshold_rate=0.50,
        rolling_window_size=6,
        base_cooldown_seconds=0.05,
        max_cooldown_seconds=0.5
    )

    assert cb.state == CircuitState.CLOSED

    # Successful calls keep state CLOSED
    res = cb.execute(lambda: "SUCCESS")
    assert res == "SUCCESS"
    assert cb.state == CircuitState.CLOSED

    # Simulate 4 consecutive failures
    def failing_fn():
        raise ConnectionResetError("API Unreachable")

    for _ in range(4):
        try:
            cb.execute(failing_fn)
        except (ConnectionResetError, CircuitBreakerOpenError):
            pass

    # Circuit should now be OPEN!
    assert cb.state == CircuitState.OPEN
    assert cb.trip_count == 1

    # While OPEN, immediate calls trigger fallback without touching network
    fallback_result = cb.execute(failing_fn, fallback=lambda: "FALLBACK_OFFLINE_CACHE")
    assert fallback_result == "FALLBACK_OFFLINE_CACHE"

    # Wait for cooldown to expire (50ms)
    import time
    time.sleep(0.06)

    # Next attempt transitions to HALF_OPEN
    recovery_result = cb.execute(lambda: "RECOVERED")
    assert recovery_result == "RECOVERED"
    # Successful execution closes circuit back to CLOSED
    assert cb.state == CircuitState.CLOSED
    assert cb.trip_count == 0


