import pytest
import json


def test_recipe_runner_initialization():
    """Test SmartRecipeRunner initialization."""
    # Mock environment variables
    import os
    os.environ['GADI_USER'] = 'test_user'
    os.environ['GADI_KEY'] = 'test_key'
    os.environ['SCRIPTS_DIR'] = '/tmp/scripts'
    
    # Import and create the runner
    import importlib.util
    spec = importlib.util.spec_from_file_location("recipe_runner", 
        os.path.join(os.path.dirname(__file__), '..', 'lib', 'recipe-runner.py'))
    recipe_runner_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recipe_runner_module)
    
    runner = recipe_runner_module.SmartRecipeRunner()
    
    # Test that basic attributes exist
    assert hasattr(runner, 'log_dir')
    assert str(runner.log_dir).endswith('logs')


def test_check_recent_runs(recipe_runner):
    """Test checking recent runs."""
    if not hasattr(recipe_runner, 'check_recent_runs'):
        pytest.skip("SmartRecipeRunner.check_recent_runs not available")
        
    result = recipe_runner.check_recent_runs('test_recipe')
    # Currently always returns True
    assert result is True


@pytest.mark.parametrize("version,expected_path_contains", [
    ('main', ('ESMValTool-main', 'esmvaltool/recipes')),
    ('latest', ('ESMValTool-main', 'esmvaltool/recipes')),
    ('v2.13.0', ('ESMValTool-2.13', 'esmvaltool/recipes')),
    ('v2.12.0', ('ESMValTool-2.12', 'esmvaltool/recipes')),
])
def test_determine_esmvaltool_path(recipe_runner, version, expected_path_contains):
    """Test ESMValTool path determination."""
    if not hasattr(recipe_runner, 'determine_esmvaltool_path'):
        pytest.skip("SmartRecipeRunner.determine_esmvaltool_path not available")
        
    base_path, recipe_path = recipe_runner.determine_esmvaltool_path(version)
    
    assert expected_path_contains[0] in base_path
    assert expected_path_contains[1] in recipe_path


def test_generate_pbs_script(recipe_runner, mock_config, monkeypatch):
    """Test PBS script generation."""
    
    if not hasattr(recipe_runner, 'generate_pbs_script'):
        pytest.skip("SmartRecipeRunner.generate_pbs_script not available")
    
    script = recipe_runner.generate_pbs_script(
        recipe_name='test_recipe',
        config=mock_config,
        recipe_type='esmvaltool',
        esmvaltool_version='main',
        conda_module='conda/analysis3',
        project='w40'
    )
    
    assert isinstance(script, str)
    assert '#PBS' in script
    assert 'test_recipe' in script
    assert '#PBS -P w40' in script


@pytest.mark.parametrize("project", ['w40', 'kj13', 'fs38', 'oi10'])
def test_project_parameter(recipe_runner, mock_config, project):
    """Test that the project parameter is correctly set in PBS scripts."""
    
    if not hasattr(recipe_runner, 'generate_pbs_script'):
        pytest.skip("SmartRecipeRunner.generate_pbs_script not available")
    
    script = recipe_runner.generate_pbs_script(
        recipe_name='test_recipe',
        config=mock_config,
        recipe_type='esmvaltool',
        esmvaltool_version='main',
        conda_module='conda/analysis3',
        project=project
    )
    
    assert isinstance(script, str)
    assert f'#PBS -P {project}' in script

@pytest.mark.parametrize("config", [
    {'queue': 'copyq', 'memory': '32GB', 'walltime': '2:00:00'},
    {'queue': 'normal', 'memory': '64GB', 'walltime': '12:00:00'},
    {'queue': 'hugemem', 'memory': '128GB', 'walltime': '24:00:00'}
])
@pytest.mark.integration
def test_resource_validation(config):
    """Test resource parameter validation."""
    # Validate memory format (should end with GB or MB)
    memory = config['memory']
    assert memory.endswith('GB') or memory.endswith('MB') or memory.endswith('gb') or memory.endswith('mb')
    
    # Validate walltime format (HH:MM:SS)
    walltime = config['walltime']
    import re
    assert re.match(r'^\d{1,2}:\d{2}:\d{2}$', walltime)
    
    # Validate queue
    queue = config['queue']
    assert queue in ['copyq', 'normal', 'express', 'hugemem']


@pytest.mark.slow
def test_full_workflow_dry_run(recipe_runner):
    """Test a complete workflow in dry run mode."""
    
    mock_config = {
        'queue': 'normal',
        'memory': '128gb',
        'walltime': '12:00:00',
        'group': 'heavy'
    }
    
    # Convert config to JSON string
    config_json = json.dumps(mock_config)
    
    result = recipe_runner.run(
        recipe_name='complex_recipe',
        config_json=config_json,
        recipe_type='esmvaltool',
        esmvaltool_version='main',
        conda_module='conda/analysis3',
        project='w40'
    )
    
    # Should complete successfully 
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] == 'pbs-generated'


if __name__ == '__main__':
    pytest.main([__file__])
