import os
import sys
import pytest

# Ensure headless Qt across all test runs
os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(autouse=True)
def cleanup_qt_widgets():
    """Ensure any orphaned Qt widgets created during a test are closed before the next test."""
    yield
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            app.closeAllWindows()
            app.processEvents()
    except Exception:
        pass


def pytest_sessionfinish(session, exitstatus):
    status = int(exitstatus)
    print(f"\n[SESSION FINISH] exitstatus={status}", flush=True)
    os._exit(status)
