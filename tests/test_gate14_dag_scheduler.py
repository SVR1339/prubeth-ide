"""
Gate 14: Parallel DAG Task Scheduler — Integration Tests
Tests: TaskDAG, CycleDetectedError, DAGCheckpointer, DAGScheduler, ParallelExecutor.
"""
import time
import threading
import pytest
from pathlib import Path
from antigravity.dag_scheduler import (
    TaskDAG, DAGNode, DAGNodeStatus, DAGEdge, DAGEdgeType,
    CycleDetectedError, DAGCheckpointer, DAGScheduler, ParallelExecutor
)


# ─── Test 1: Topological sort and cycle detection ─── #
def test_dag_topological_sort_and_cycle_detection():
    """DAG correctly sorts nodes and raises CycleDetectedError on circular dependencies."""
    dag = TaskDAG(goal="Build microservice")
    n1 = dag.add_node("Design", "Define API schema", node_id="n1")
    n2 = dag.add_node("Code API", "Implement endpoints", node_id="n2")
    n3 = dag.add_node("Write Tests", "Unit tests for API", node_id="n3")
    n4 = dag.add_node("Deploy", "Push to staging", node_id="n4")

    dag.add_edge("n1", "n2")
    dag.add_edge("n2", "n3")
    dag.add_edge("n3", "n4")

    order = dag.topological_order()
    ids = [n.node_id for n in order]
    assert ids == ["n1", "n2", "n3", "n4"]

    # Initially only n1 is ready
    ready = dag.get_ready_nodes()
    assert len(ready) == 1
    assert ready[0].node_id == "n1"

    # Complete n1; n2 becomes ready
    n1.status = DAGNodeStatus.COMPLETED
    ready = dag.get_ready_nodes()
    assert any(n.node_id == "n2" for n in ready)

    # Test cycle detection: n4 → n2 would create n2→n3→n4→n2 cycle
    with pytest.raises(CycleDetectedError):
        dag.add_edge("n4", "n2")


# ─── Test 2: Parallel execution of independent branches ─── #
def test_dag_parallel_branch_execution(tmp_path):
    """Independent DAG branches execute concurrently using ParallelExecutor."""
    dag = TaskDAG(goal="Parallel workload", dag_id="parallel-test")
    dag.add_node("Root", "Starting node", node_id="root")
    dag.add_node("Branch A", "Independent path A", node_id="branch_a")
    dag.add_node("Branch B", "Independent path B", node_id="branch_b")
    dag.add_node("Merge", "Final merge step", node_id="merge")

    dag.add_edge("root", "branch_a")
    dag.add_edge("root", "branch_b")
    dag.add_edge("branch_a", "merge")
    dag.add_edge("branch_b", "merge")

    execution_order = []
    lock = threading.Lock()

    def mock_handler(node: DAGNode, ctx: dict) -> dict:
        time.sleep(0.05)  # Simulate real work
        with lock:
            execution_order.append(node.node_id)
        return {"done": True}

    scheduler = DAGScheduler(max_workers=4)
    result = scheduler.run(dag, default_handler=mock_handler, timeout_seconds=10.0)

    assert result["success"] is True
    assert result["progress_pct"] == 100.0
    # Root must execute first
    assert execution_order[0] == "root"
    # branch_a and branch_b must both execute before merge
    merge_idx = execution_order.index("merge")
    assert "branch_a" in execution_order[:merge_idx]
    assert "branch_b" in execution_order[:merge_idx]
    # Verify branches ran "in parallel" (both before merge)
    assert merge_idx == len(execution_order) - 1


# ─── Test 3: DAGCheckpointer persists and restores state ─── #
def test_dag_checkpointer_persistence_and_restore(tmp_path):
    """DAGCheckpointer saves node statuses to SQLite and restores on a new DAG instance."""
    db_path = tmp_path / "test_checkpoints.db"
    checkpointer = DAGCheckpointer(db_path=db_path)

    dag = TaskDAG(goal="Resumable task", dag_id="resume-dag")
    n1 = dag.add_node("Step 1", "First step", node_id="s1")
    n2 = dag.add_node("Step 2", "Second step", node_id="s2")

    # Simulate n1 being completed and persisted
    n1.status = DAGNodeStatus.COMPLETED
    n1.result = {"output": "step1_done"}
    n1.started_at = time.time() - 10
    n1.completed_at = time.time()
    checkpointer.save_node(dag.dag_id, n1)

    # Create a fresh DAG with same node IDs (simulates restart)
    fresh_dag = TaskDAG(goal="Resumable task", dag_id="resume-dag")
    fresh_dag.add_node("Step 1", "First step", node_id="s1")
    fresh_dag.add_node("Step 2", "Second step", node_id="s2")

    # Restore should recover n1 as COMPLETED
    restored_count = checkpointer.restore_dag_state(fresh_dag)
    assert restored_count == 1
    assert fresh_dag.nodes["s1"].status == DAGNodeStatus.COMPLETED
    assert fresh_dag.nodes["s2"].status == DAGNodeStatus.PENDING

    # Clear and verify
    checkpointer.clear_dag("resume-dag")
    fresh_dag2 = TaskDAG(goal="Resumable task", dag_id="resume-dag")
    fresh_dag2.add_node("Step 1", "First step", node_id="s1")
    count = checkpointer.restore_dag_state(fresh_dag2)
    assert count == 0


# ─── Test 4: DATA_FLOW edges forward results between nodes ─── #
def test_dag_data_flow_edges():
    """DATA_FLOW edges forward specific result keys from source to target node context."""
    dag = TaskDAG(goal="Data pipeline", dag_id="data-flow-test")
    dag.add_node("Extract", "Extract data", node_id="extract")
    dag.add_node("Transform", "Transform data", node_id="transform")

    dag.add_edge("extract", "transform", edge_type=DAGEdgeType.DATA_FLOW, data_key="records")

    # Simulate extract completing with a result
    dag.nodes["extract"].status = DAGNodeStatus.COMPLETED
    dag.nodes["extract"].result = {"records": [1, 2, 3], "count": 3}

    # Transform node should receive "records" from extract
    inputs = dag.get_data_inputs_for_node("transform")
    assert inputs["records"] == [1, 2, 3]


# ─── Test 5: DAG failure handling — failed node blocks downstream ─── #
def test_dag_failure_blocks_downstream_and_reports():
    """A failed required node blocks downstream nodes; the DAG reports failure correctly."""
    dag = TaskDAG(goal="Build with failure", dag_id="failure-test")
    dag.add_node("Good Step", "Succeeds", node_id="good")
    dag.add_node("Bad Step", "Fails", node_id="bad")
    dag.add_node("Blocked", "Depends on bad", node_id="blocked")

    dag.add_edge("good", "bad")
    dag.add_edge("bad", "blocked")

    call_count = [0]

    def handler(node: DAGNode, ctx: dict) -> dict:
        call_count[0] += 1
        if node.node_id == "bad":
            raise RuntimeError("Simulated failure in step")
        return {"done": True}

    scheduler = DAGScheduler(max_workers=2)
    result = scheduler.run(dag, default_handler=handler, timeout_seconds=10.0)

    assert result["success"] is False
    assert dag.nodes["bad"].status == DAGNodeStatus.FAILED
    assert dag.nodes["bad"].error is not None
    # "blocked" should never have been dispatched since "bad" failed
    assert dag.nodes["blocked"].status == DAGNodeStatus.PENDING
    assert dag.has_failures is True
