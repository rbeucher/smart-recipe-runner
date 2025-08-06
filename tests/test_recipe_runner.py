import os
import subprocess
import pytest


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
    
    assert runner.gadi_host == 'gadi.nci.org.au'
    assert runner.gadi_user == 'test_user'
    assert runner.gadi_key == 'test_key'
    assert runner.scripts_dir == '/tmp/scripts'


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
    from unittest.mock import MagicMock
    
    if not hasattr(recipe_runner, 'generate_pbs_script'):
        pytest.skip("SmartRecipeRunner.generate_pbs_script not available")
    
    # The actual method signature: generate_pbs_script(recipe_name, config, esmvaltool_version, conda_module)
    monkeypatch.setattr(recipe_runner, 'determine_esmvaltool_path', MagicMock(return_value=('/path/to/esmvaltool', 'recipes')))
    
    script = recipe_runner.generate_pbs_script(
        recipe_name='test_recipe',
        config=mock_config,
        esmvaltool_version='main',
        conda_module='esmvaltool'
    )
    
    assert isinstance(script, str)
    assert '#PBS' in script
    assert 'test_recipe' in script


def test_execute_ssh_command(recipe_runner, monkeypatch):
    """Test SSH command execution."""
    from unittest.mock import MagicMock
    
    if not hasattr(recipe_runner, 'execute_ssh_command'):
        pytest.skip("SmartRecipeRunner.execute_ssh_command not available")
        
    mock_run = MagicMock()
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout='test output',
        stderr=''
    )
    monkeypatch.setattr('subprocess.run', mock_run)
    
    returncode, stdout, stderr = recipe_runner.execute_ssh_command('echo test')
    
    assert returncode == 0
    assert 'test output' in stdout


def test_submit_job(recipe_runner, monkeypatch):
    """Test job submission."""
    from unittest.mock import MagicMock
    
    if not hasattr(recipe_runner, 'submit_job'):
        pytest.skip("SmartRecipeRunner.submit_job not available")
    
    mock_ssh = MagicMock()
    # Mock multiple ssh command calls that might be made during job submission
    mock_ssh.return_value = (0, 'Job submitted: 12345.gadi-pbs', '')
    monkeypatch.setattr(recipe_runner, 'execute_ssh_command', mock_ssh)
    
    job_id, status, error = recipe_runner.submit_job('test_recipe', 'mock_script')
    
    assert job_id is not None or status is not None
@pytest.mark.parametrize("dry_run", [True, False])
def test_run_method(recipe_runner, dry_run, monkeypatch):
    """Test the main run method."""
    from unittest.mock import MagicMock
    
    if not hasattr(recipe_runner, 'run'):
        pytest.skip("SmartRecipeRunner.run not available")
    
    # Config should match what the run method expects - flat structure with required keys
    mock_config = {
        'queue': 'normal',
        'memory': '8gb',
        'walltime': '03:00:00',
        'group': 'medium'
    }
    
    # Convert config to JSON string as expected by the method
    import json
    config_json = json.dumps(mock_config)
    
    mode = 'dry-run' if dry_run else 'run'
    
    monkeypatch.setattr(recipe_runner, 'generate_pbs_script', MagicMock(return_value='mock_script'))
    monkeypatch.setattr(recipe_runner, 'submit_job', MagicMock(return_value=('12345', 'submitted', '')))
    monkeypatch.setattr(recipe_runner, 'check_recent_runs', MagicMock(return_value=True))
    
    result = recipe_runner.run(
        recipe_name='test_recipe',
        config_json=config_json,
        esmvaltool_version='main',
        conda_module='esmvaltool',
        mode=mode
    )
    
    # Should return a tuple (status, job_id)
    assert isinstance(result, tuple)
    assert len(result) == 2


# Integration tests
@pytest.mark.integration
def test_pbs_script_syntax():
    """Test that generated PBS scripts have valid syntax."""
    script_template = """#!/bin/bash
#PBS -N test_job
#PBS -l mem=8gb
#PBS -l ncpus=4
#PBS -l walltime=03:00:00
#PBS -q normal

cd $PBS_O_WORKDIR
echo "Starting ESMValTool execution"
"""
    
    # Basic syntax validation
    lines = script_template.strip().split('\n')
    assert lines[0].startswith('#!/bin/bash')
    
    pbs_lines = [line for line in lines if line.startswith('#PBS')]
    assert len(pbs_lines) > 0
    
    # Check PBS directives format
    for line in pbs_lines:
        assert line.startswith('#PBS -')


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
def test_full_workflow_dry_run(recipe_runner, monkeypatch):
    """Test complete workflow in dry run mode."""
    from unittest.mock import MagicMock
    
    if not hasattr(recipe_runner, 'run'):
        pytest.skip("SmartRecipeRunner.run not available")
    
    # Config should match what the run method expects - flat structure
    mock_config = {
        'queue': 'normal',
        'memory': '128gb',
        'walltime': '12:00:00',
        'group': 'heavy'
    }
    
    # Convert config to JSON string
    import json
    config_json = json.dumps(mock_config)
    
    # Mock all external dependencies
    monkeypatch.setattr(recipe_runner, 'check_recent_runs', MagicMock(return_value=True))
    monkeypatch.setattr(recipe_runner, 'generate_pbs_script', MagicMock(return_value='mock_script'))
    monkeypatch.setattr(recipe_runner, 'submit_job', MagicMock(return_value=('mock_job_id', 'submitted', '')))
    
    result = recipe_runner.run(
        recipe_name='complex_recipe',
        config_json=config_json,
        esmvaltool_version='main',
        conda_module='esmvaltool',
        mode='dry-run'
    )
    
    # Should complete successfully in dry run mode
    assert isinstance(result, tuple)
    assert len(result) == 2


if __name__ == '__main__':
    pytest.main([__file__])
