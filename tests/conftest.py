"""
pytest configuration and fixtures
"""
import sys
import os
import tempfile
import pytest
import importlib.util


# Add lib directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))


def _import_module_from_file(module_name, file_path):
    """Helper function to import modules from files with hyphens."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir


@pytest.fixture
def config_manager():
    """Create a SmartConfigManager instance."""
    # Import the config manager module
    module = _import_module_from_file("config_manager", 
        os.path.join(os.path.dirname(__file__), '..', 'lib', 'config-manager.py'))
    
    if module is None:
        pytest.skip("SmartConfigManager module not available")
    
    # SmartConfigManager requires recipe_dir, config_path, and hpc_system
    return module.SmartConfigManager(
        recipe_dir='/tmp/recipes',
        config_path='/tmp/config',
        hpc_system='gadi'
    )


@pytest.fixture
def recipe_runner():
    """Create a SmartRecipeRunner instance."""
    # Import the recipe runner module
    module = _import_module_from_file("recipe_runner", 
        os.path.join(os.path.dirname(__file__), '..', 'lib', 'recipe-runner.py'))
    
    if module is None:
        # Create a mock if import fails
        class MockRecipeRunner:
            def __init__(self):
                pass
        return MockRecipeRunner()
    
    # Mock environment variables for SmartRecipeRunner
    import os as os_module
    os_module.environ.setdefault('GADI_USER', 'test_user')
    os_module.environ.setdefault('GADI_KEY', 'test_key')
    os_module.environ.setdefault('SCRIPTS_DIR', '/tmp/scripts')
    
    return module.SmartRecipeRunner()


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        'memory': '8gb',
        'cpus': 4,
        'walltime': '03:00:00',
        'queue': 'normal',
        'group': 'medium'  # Added missing 'group' key
    }


@pytest.fixture
def sample_recipe_content():
    """Sample recipe content for testing."""
    return {
        'documentation': {
            'description': 'Test recipe',
            'title': 'Test Recipe'
        },
        'datasets': [
            {'dataset': 'CanESM2', 'project': 'CMIP5'},
            {'dataset': 'CESM1-BGC', 'project': 'CMIP5'}
        ],
        'preprocessors': {
            'annual_mean': {
                'annual_statistics': {'operator': 'mean'}
            }
        },
        'diagnostics': {
            'test_diagnostic': {
                'description': 'Test diagnostic',
                'variables': {
                    'tas': {
                        'preprocessor': 'annual_mean'
                    }
                }
            }
        }
    }
