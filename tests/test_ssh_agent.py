#!/usr/bin/env python3
"""
Test SSH agent functionality for password-protected keys.
"""

import os
import sys
import tempfile
import subprocess
from unittest.mock import patch, MagicMock

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

# Import with proper module name
import importlib.util
spec = importlib.util.spec_from_file_location("recipe_runner", 
    os.path.join(os.path.dirname(__file__), '..', 'lib', 'recipe-runner.py'))
recipe_runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe_runner)
SmartRecipeRunner = recipe_runner.SmartRecipeRunner


def test_ssh_agent_setup():
    """Test SSH agent setup with password-protected key."""
    
    # Create a temporary key file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
        f.write("""-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAACmFlczI1Ni1jdHIAAAAGYmNyeXB0AAAAGAAAABA
test_encrypted_key_content_here
-----END OPENSSH PRIVATE KEY-----""")
        test_key_path = f.name
    
    try:
        # Set up environment for testing
        os.environ['GADI_USER'] = 'test_user'
        os.environ['GADI_KEY'] = test_key_path
        os.environ['GADI_KEY_PASSPHRASE'] = 'test_passphrase'
        os.environ['SCRIPTS_DIR'] = '/tmp/test_scripts'
        
        # Test SSH agent setup (mock the subprocess calls)
        with patch('subprocess.run') as mock_run:
            # Mock ssh-agent output
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="SSH_AUTH_SOCK=/tmp/ssh-agent.123; export SSH_AUTH_SOCK;\nSSH_AGENT_PID=12345; export SSH_AGENT_PID;\n"
            )
            
            runner = SmartRecipeRunner(hpc_system='gadi')
            
            # Check that environment variables are properly handled
            assert runner.gadi_user == 'test_user'
            assert runner.gadi_key == test_key_path
            assert runner.gadi_key_passphrase == 'test_passphrase'
            
        print("✅ SSH agent test passed")
        
    finally:
        # Clean up
        os.unlink(test_key_path)
        # Clean up environment
        for key in ['GADI_USER', 'GADI_KEY', 'GADI_KEY_PASSPHRASE', 'SCRIPTS_DIR']:
            if key in os.environ:
                del os.environ[key]


def test_ssh_command_without_passphrase():
    """Test SSH command execution without passphrase."""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
        f.write("-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key\n-----END OPENSSH PRIVATE KEY-----")
        test_key_path = f.name
    
    try:
        os.environ['GADI_USER'] = 'test_user'
        os.environ['GADI_KEY'] = test_key_path
        os.environ['SCRIPTS_DIR'] = '/tmp/test_scripts'
        # No GADI_KEY_PASSPHRASE set
        
        runner = SmartRecipeRunner(hpc_system='gadi')
        
        # Mock subprocess for SSH command
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="test output", stderr="")
            
            result = runner.execute_ssh_command("echo test")
            assert result[0] == 0  # Success return code
            
        print("✅ SSH command test (no passphrase) passed")
        
    finally:
        os.unlink(test_key_path)
        for key in ['GADI_USER', 'GADI_KEY', 'SCRIPTS_DIR']:
            if key in os.environ:
                del os.environ[key]


if __name__ == '__main__':
    test_ssh_agent_setup()
    test_ssh_command_without_passphrase()
    print("🎉 All SSH agent tests passed!")
