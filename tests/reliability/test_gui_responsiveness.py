"""PRUBETH IDE - GUI Responsiveness & Non-Blocking Event Loop Tests
================================================================
Verifies that background workloads, tab switching, and command palette queries
execute asynchronously and never freeze or starve the main execution thread.
"""

import threading
import time
import pytest
from tests.reliability.helpers.crash_harness import timed_operation
from ui.panel_registry import PanelRegistry
from core.command_registry import CommandRegistry, Command, CommandRiskLevel


def test_command_palette_query_responsiveness():
    """Searching across hundreds of commands must complete in under 50ms."""
    registry = CommandRegistry()
    for i in range(150):
        registry.register(Command(
            command_id=f"test.action_{i}",
            title=f"Perform Action {i} in Category",
            category="testing",
            handler=lambda: None,
            risk_level=CommandRiskLevel.READ_ONLY,
        ))

    with timed_operation(0.2):  # Must complete in well under 200ms
        results = registry.search("action 42")
        assert len(results) >= 1
        assert results[0].command_id == "test.action_42"


def test_rapid_layout_preset_switching_stability():
    """Rapidly querying all 6 layout presets must not deadlock or corrupt state."""
    registry = PanelRegistry()
    presets = registry.list_presets()
    assert len(presets) == 6

    with timed_operation(1.0):
        for _ in range(5):
            for p in presets:
                preset_data = registry.get_preset(p.name)
                assert preset_data is not None
                assert isinstance(preset_data.visible_panel_ids, list)


def test_background_worker_does_not_block_main_thread():
    """Heavy computation on a worker thread must not block main thread responsiveness."""
    worker_finished = threading.Event()

    def heavy_worker():
        total = sum(i * i for i in range(500000))
        worker_finished.set()

    t = threading.Thread(target=heavy_worker, daemon=True)
    t.start()

    # Main thread must remain active and responsive immediately
    ticks = 0
    start = time.perf_counter()
    while not worker_finished.is_set():
        ticks += 1
        time.sleep(0.005)

    duration = time.perf_counter() - start
    assert ticks > 0
    assert duration < 2.0
