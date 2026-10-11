"""
PRUBETH IDE — PRUBETH Horizon Parallel DAG Task Scheduler
Upgrades MissionControl from sequential to truly parallel subagent DAG execution.

Research Foundation:
  - ChatDev, MetaGPT, and DAG Scheduler studies:
    Single monolithic agents suffer from context pollution. Decompose into
    specialized subagents that run *in parallel* along independent DAG branches.
  - SWE-bench: Real autonomous issue resolution requires multi-step planning
    where "code writing" doesn't block "test framework setup" (parallel branches).

Architecture:
  1. DAGNode:         Typed task node with status, dependencies, and result storage
  2. DAGEdge:         Typed dependency edge (REQUIRED, OPTIONAL, DATA_FLOW)
  3. TaskDAG:         Full directed acyclic graph with topological sort & cycle detection
  4. DAGScheduler:    Traverses the DAG, dispatching ready nodes to the executor pool
  5. ParallelExecutor: Thread-pool-based concurrent executor for independent DAG branches
  6. DAGCheckpointer: SQLite-backed per-node checkpoint/resume for IDE restart recovery
"""
import time
import uuid
import threading
import sqlite3
import json
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Set, Tuple


class DAGNodeStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"         # All dependencies satisfied
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"     # Skipped due to optional dependency failure


class DAGEdgeType(str, Enum):
    REQUIRED = "required"          # Target cannot start until source completes
    OPTIONAL = "optional"          # Target starts even if source fails
    DATA_FLOW = "data_flow"        # Source output is passed as input to target


class CycleDetectedError(ValueError):
    """Raised when a cycle is detected in the DAG."""
    pass


@dataclass
class DAGNode:
    """A single task node in the execution DAG."""
    node_id: str
    title: str
    description: str
    assigned_role: str = "generalist"
    status: DAGNodeStatus = DAGNodeStatus.PENDING
    handler: Optional[Callable[["DAGNode", Dict[str, Any]], Dict[str, Any]]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return round(self.completed_at - self.started_at, 3)
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "title": self.title,
            "description": self.description,
            "assigned_role": self.assigned_role,
            "status": self.status.value,
            "error": self.error,
            "duration_seconds": self.duration_seconds(),
            "result_keys": list(self.result.keys()) if self.result else []
        }


@dataclass
class DAGEdge:
    """A directed dependency edge between two DAGNodes."""
    source_id: str
    target_id: str
    edge_type: DAGEdgeType = DAGEdgeType.REQUIRED
    data_key: Optional[str] = None   # For DATA_FLOW: which result key to forward


class TaskDAG:
    """
    Full directed acyclic graph representation for multi-agent task decomposition.
    Provides topological ordering, cycle detection, and readiness tracking.
    """

    def __init__(self, goal: str, dag_id: Optional[str] = None):
        self.dag_id = dag_id or f"dag-{uuid.uuid4().hex[:8]}"
        self.goal = goal
        self.nodes: Dict[str, DAGNode] = {}
        self.edges: List[DAGEdge] = []
        self.created_at = time.time()

    def add_node(self, title: str, description: str, assigned_role: str = "generalist",
                 node_id: Optional[str] = None,
                 handler: Optional[Callable] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> DAGNode:
        """Adds a task node to the DAG."""
        nid = node_id or f"node-{uuid.uuid4().hex[:6]}"
        node = DAGNode(
            node_id=nid,
            title=title,
            description=description,
            assigned_role=assigned_role,
            handler=handler,
            metadata=metadata or {}
        )
        self.nodes[nid] = node
        return node

    def add_edge(self, source_id: str, target_id: str,
                 edge_type: DAGEdgeType = DAGEdgeType.REQUIRED,
                 data_key: Optional[str] = None) -> DAGEdge:
        """Adds a directed dependency edge. Raises CycleDetectedError if a cycle results."""
        if source_id not in self.nodes:
            raise KeyError(f"Source node '{source_id}' not found in DAG")
        if target_id not in self.nodes:
            raise KeyError(f"Target node '{target_id}' not found in DAG")
        edge = DAGEdge(source_id=source_id, target_id=target_id, edge_type=edge_type, data_key=data_key)
        self.edges.append(edge)
        # Validate no cycle was introduced
        try:
            self.topological_order()
        except CycleDetectedError:
            self.edges.remove(edge)
            raise
        return edge

    def _build_adjacency(self) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
        """Returns (successors, in-degree) maps."""
        successors: Dict[str, List[str]] = {nid: [] for nid in self.nodes}
        in_degree: Dict[str, int] = {nid: 0 for nid in self.nodes}
        for edge in self.edges:
            successors[edge.source_id].append(edge.target_id)
            in_degree[edge.target_id] += 1
        return successors, in_degree

    def topological_order(self) -> List[DAGNode]:
        """Returns nodes in topological execution order (Kahn's algorithm)."""
        successors, in_degree = self._build_adjacency()
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        queue.sort()  # Deterministic ordering
        result: List[DAGNode] = []
        while queue:
            nid = queue.pop(0)
            result.append(self.nodes[nid])
            for successor in sorted(successors[nid]):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)
        if len(result) != len(self.nodes):
            raise CycleDetectedError(
                f"Cycle detected in DAG '{self.dag_id}'. "
                f"Processed {len(result)}/{len(self.nodes)} nodes."
            )
        return result

    def get_ready_nodes(self) -> List[DAGNode]:
        """Returns nodes whose required dependencies are all COMPLETED."""
        # Build dependency map
        deps: Dict[str, List[DAGEdge]] = {nid: [] for nid in self.nodes}
        for edge in self.edges:
            deps[edge.target_id].append(edge)

        ready = []
        for nid, node in self.nodes.items():
            if node.status != DAGNodeStatus.PENDING:
                continue
            node_deps = deps[nid]
            all_ready = True
            for edge in node_deps:
                src = self.nodes.get(edge.source_id)
                if not src:
                    continue
                if edge.edge_type == DAGEdgeType.REQUIRED:
                    if src.status not in (DAGNodeStatus.COMPLETED,):
                        all_ready = False
                        break
            if all_ready:
                ready.append(node)
        return ready

    def get_data_inputs_for_node(self, node_id: str) -> Dict[str, Any]:
        """Collects DATA_FLOW edge outputs to pass as inputs to a node."""
        inputs = {}
        for edge in self.edges:
            if edge.target_id == node_id and edge.edge_type == DAGEdgeType.DATA_FLOW:
                src = self.nodes.get(edge.source_id)
                if src and src.result and edge.data_key:
                    inputs[edge.data_key] = src.result.get(edge.data_key)
        return inputs

    @property
    def is_complete(self) -> bool:
        return all(n.status in (DAGNodeStatus.COMPLETED, DAGNodeStatus.SKIPPED, DAGNodeStatus.FAILED)
                   for n in self.nodes.values())

    @property
    def has_failures(self) -> bool:
        return any(n.status == DAGNodeStatus.FAILED for n in self.nodes.values())

    def progress_pct(self) -> float:
        if not self.nodes:
            return 100.0
        done = sum(1 for n in self.nodes.values()
                   if n.status in (DAGNodeStatus.COMPLETED, DAGNodeStatus.SKIPPED, DAGNodeStatus.FAILED))
        return round(done / len(self.nodes) * 100, 1)

    def to_summary(self) -> Dict[str, Any]:
        return {
            "dag_id": self.dag_id,
            "goal": self.goal,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "progress_pct": self.progress_pct(),
            "is_complete": self.is_complete,
            "has_failures": self.has_failures,
            "nodes": [n.to_dict() for n in self.nodes.values()]
        }


# ---------------------------------------------------------------------------
# DAG Checkpointer — SQLite-backed per-node checkpoint/resume
# ---------------------------------------------------------------------------

class DAGCheckpointer:
    """Persists DAG execution state to SQLite for recovery after IDE restart."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".local_ai_studio_pro" / "dag_checkpoints.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(db_path)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dag_nodes (
                    dag_id TEXT,
                    node_id TEXT,
                    status TEXT,
                    result TEXT,
                    error TEXT,
                    started_at REAL,
                    completed_at REAL,
                    PRIMARY KEY (dag_id, node_id)
                )
            """)
            conn.commit()

    def save_node(self, dag_id: str, node: DAGNode):
        """Persists a node's current execution state."""
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO dag_nodes (dag_id, node_id, status, result, error, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (dag_id, node.node_id, node.status.value,
                  json.dumps(node.result) if node.result else None,
                  node.error, node.started_at, node.completed_at))
            conn.commit()

    def restore_dag_state(self, dag: TaskDAG) -> int:
        """Restores node statuses from checkpointed data. Returns number of nodes restored."""
        restored = 0
        try:
            with self._conn() as conn:
                rows = conn.execute("SELECT * FROM dag_nodes WHERE dag_id = ?", (dag.dag_id,)).fetchall()
                for row in rows:
                    node = dag.nodes.get(row["node_id"])
                    if node:
                        node.status = DAGNodeStatus(row["status"])
                        node.error = row["error"]
                        node.started_at = row["started_at"]
                        node.completed_at = row["completed_at"]
                        if row["result"]:
                            try:
                                node.result = json.loads(row["result"])
                            except Exception:
                                pass
                        restored += 1
        except Exception:
            pass
        return restored

    def clear_dag(self, dag_id: str):
        """Clears all checkpoint data for a completed DAG."""
        with self._conn() as conn:
            conn.execute("DELETE FROM dag_nodes WHERE dag_id = ?", (dag_id,))
            conn.commit()


# ---------------------------------------------------------------------------
# DAG Scheduler & Parallel Executor
# ---------------------------------------------------------------------------

class ParallelExecutor:
    """Thread-pool executor for running independent DAG branches in parallel."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._executor: Optional[ThreadPoolExecutor] = None
        self._active_futures: Dict[str, Future] = {}
        self._lock = threading.Lock()

    def start(self):
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="dag-worker")

    def stop(self, wait: bool = True):
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None

    def submit(self, node: DAGNode, handler: Callable, context: Dict[str, Any]) -> Future:
        """Submits a node handler for parallel execution."""
        if not self._executor:
            self.start()
        future = self._executor.submit(handler, node, context)
        with self._lock:
            self._active_futures[node.node_id] = future
        return future

    def get_completed(self) -> List[Tuple[str, Optional[Dict], Optional[str]]]:
        """Returns (node_id, result, error) for completed futures."""
        completed = []
        with self._lock:
            done_ids = [nid for nid, f in self._active_futures.items() if f.done()]
        for nid in done_ids:
            with self._lock:
                future = self._active_futures.pop(nid, None)
            if future:
                if future.exception():
                    completed.append((nid, None, str(future.exception())))
                else:
                    completed.append((nid, future.result(), None))
        return completed

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._active_futures)


class DAGScheduler:
    """
    Traverses a TaskDAG, dispatching ready nodes to the ParallelExecutor pool.
    Integrates with DAGCheckpointer for recovery after restarts.
    """

    def __init__(self, max_workers: int = 4, checkpointer: Optional[DAGCheckpointer] = None,
                 poll_interval: float = 0.05):
        self.executor = ParallelExecutor(max_workers=max_workers)
        self.checkpointer = checkpointer
        self.poll_interval = poll_interval
        self._on_node_complete: Optional[Callable[[DAGNode], None]] = None
        self._on_node_failed: Optional[Callable[[DAGNode, str], None]] = None

    def set_callbacks(self,
                      on_complete: Optional[Callable[[DAGNode], None]] = None,
                      on_failed: Optional[Callable[[DAGNode, str], None]] = None):
        """Sets optional event callbacks for node completion/failure."""
        self._on_node_complete = on_complete
        self._on_node_failed = on_failed

    def run(self, dag: TaskDAG, default_handler: Optional[Callable] = None,
            timeout_seconds: float = 300.0) -> Dict[str, Any]:
        """
        Executes the DAG with parallel branch execution.
        Returns a summary dict with success status and execution log.
        """
        start_time = time.time()

        # Restore from checkpoint if available
        if self.checkpointer:
            self.checkpointer.restore_dag_state(dag)

        self.executor.start()
        execution_log: List[Dict[str, Any]] = []
        in_flight: Set[str] = set()

        try:
            while not dag.is_complete:
                if time.time() - start_time > timeout_seconds:
                    break

                # Check for completed futures
                for node_id, result, error in self.executor.get_completed():
                    in_flight.discard(node_id)
                    node = dag.nodes.get(node_id)
                    if not node:
                        continue
                    node.completed_at = time.time()
                    if error:
                        node.status = DAGNodeStatus.FAILED
                        node.error = error
                        if self._on_node_failed:
                            self._on_node_failed(node, error)
                    else:
                        node.status = DAGNodeStatus.COMPLETED
                        node.result = result or {}
                        if self._on_node_complete:
                            self._on_node_complete(node)
                    if self.checkpointer:
                        self.checkpointer.save_node(dag.dag_id, node)
                    execution_log.append(node.to_dict())

                # Dispatch all newly-ready nodes
                ready = dag.get_ready_nodes()
                for node in ready:
                    if node.node_id in in_flight:
                        continue
                    handler = node.handler or default_handler
                    if handler is None:
                        node.status = DAGNodeStatus.SKIPPED
                        node.result = {"skipped": "No handler registered"}
                        execution_log.append(node.to_dict())
                        continue

                    node.status = DAGNodeStatus.RUNNING
                    node.started_at = time.time()
                    in_flight.add(node.node_id)
                    context = dag.get_data_inputs_for_node(node.node_id)
                    self.executor.submit(node, handler, context)

                if not in_flight and not dag.get_ready_nodes() and not dag.is_complete:
                    # All pending nodes are blocked — DAG is deadlocked (shouldn't happen after cycle check)
                    break

                time.sleep(self.poll_interval)

        finally:
            self.executor.stop(wait=True)

        duration = round(time.time() - start_time, 3)
        return {
            "success": dag.is_complete and not dag.has_failures,
            "dag_id": dag.dag_id,
            "progress_pct": dag.progress_pct(),
            "duration_seconds": duration,
            "execution_log": execution_log,
            "summary": dag.to_summary()
        }
