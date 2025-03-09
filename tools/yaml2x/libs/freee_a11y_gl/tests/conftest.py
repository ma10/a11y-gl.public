import pytest
from pathlib import Path
import shutil
import os

@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / "test_data"

@pytest.fixture
def json_data_dir(test_data_dir):
    """Return the path to the JSON test data directory."""
    return test_data_dir / "json"

@pytest.fixture
def yaml_data_dir(test_data_dir):
    """Return the path to the YAML test data directory."""
    return test_data_dir / "yaml"

@pytest.fixture
def setup_test_env(test_data_dir):
    """Setup and teardown for test environment."""
    # Setup
    yield test_data_dir
    
    # Cleanup any temporary files if needed
    temp_files = test_data_dir.glob("**/.*.tmp")
    for f in temp_files:
        if f.is_file():
            f.unlink()
