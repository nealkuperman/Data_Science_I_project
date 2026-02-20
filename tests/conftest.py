"""Pytest config: ensure project root is on PYTHONPATH so 'from source.*' works."""
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def pytest_configure(config):
    """Register custom marks."""
    config.addinivalue_line("markers", "integration: marks tests that use the test database (deselect with -m 'not integration')")
