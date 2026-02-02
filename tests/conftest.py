"""
Pytest configuration and shared fixtures.
"""

import pytest


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run live integration tests that make real API calls",
    )


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "live: marks tests as live API tests")


def pytest_collection_modifyitems(config, items):
    """Skip live tests unless --run-live is specified."""
    if config.getoption("--run-live"):
        # Run all tests including live tests
        return

    skip_live = pytest.mark.skip(reason="Need --run-live option to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
