#!/usr/bin/env python3
"""
Test script to verify SSH agent setup works in CI environments.
This simulates the actual environment where expect might not be available.
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


def test_ssh_agent_no_expect():
    """Test SSH agent setup when expect is not available (typical CI scenario)."""
    
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
        
        # Mock subprocess to simulate CI environment where expect is not available
        def mock_run(*args, **kwargs):
            cmd = args[0]
            
            # SSH agent startup - should succeed
            if cmd == ['ssh-agent', '-s']:
                return MagicMock(
                    returncode=0,
                    stdout="SSH_AUTH_SOCK=/tmp/ssh-agent.123; export SSH_AUTH_SOCK;\nSSH_AGENT_PID=12345; export SSH_AGENT_PID;\n"
                )
            
            # Check for 'which expect' - simulate not found
            elif cmd == ['which', 'expect']:
                raise subprocess.CalledProcessError(1, cmd)
            
            # Check for 'which sshpass' - simulate not found  
            elif cmd == ['which', 'sshpass']:
                raise subprocess.CalledProcessError(1, cmd)
            
            # ssh-add with SSH_ASKPASS - should succeed
            elif 'ssh-add' in cmd and len(cmd) == 2:
                return MagicMock(returncode=0, stdout="Identity added", stderr="")
            
            # Default success for other commands
            else:
                return MagicMock(returncode=0, stdout="", stderr="")
        
        with patch('subprocess.run', side_effect=mock_run):
            runner = SmartRecipeRunner(hpc_system='gadi')
            
            # Verify the SSH agent was set up successfully
            assert 'SSH_AUTH_SOCK' in os.environ
            assert 'SSH_AGENT_PID' in os.environ
            
        print("✅ SSH agent test (no expect/sshpass) passed")
        
    finally:
        # Clean up
        os.unlink(test_key_path)
        # Clean up environment
        for key in ['GADI_USER', 'GADI_KEY', 'GADI_KEY_PASSPHRASE', 'SCRIPTS_DIR', 'SSH_AUTH_SOCK', 'SSH_AGENT_PID']:
            if key in os.environ:
                del os.environ[key]


def test_ssh_agent_all_methods_fail():
    """Test SSH agent setup when all methods fail."""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
        f.write("-----BEGIN OPENSSH PRIVATE KEY-----\ntest_key\n-----END OPENSSH PRIVATE KEY-----")
        test_key_path = f.name
    
    try:
        os.environ['GADI_USER'] = 'test_user'
        os.environ['GADI_KEY'] = test_key_path
        os.environ['GADI_KEY_PASSPHRASE'] = 'test_passphrase'
        os.environ['SCRIPTS_DIR'] = '/tmp/test_scripts'
        
        # Mock subprocess to simulate all methods failing
        def mock_run(*args, **kwargs):
            cmd = args[0]
            
            # SSH agent startup - should succeed
            if cmd == ['ssh-agent', '-s']:
                return MagicMock(
                    returncode=0,
                    stdout="SSH_AUTH_SOCK=/tmp/ssh-agent.123; export SSH_AUTH_SOCK;\nSSH_AGENT_PID=12345; export SSH_AGENT_PID;\n"
                )
            
            # All tool checks fail
            elif cmd[0] == 'which':
                raise subprocess.CalledProcessError(1, cmd)
            
            # All ssh-add attempts fail
            elif 'ssh-add' in cmd:
                return MagicMock(returncode=1, stdout="", stderr="Permission denied")
            
            # Bash commands (expect scripts) fail
            elif cmd[0] == 'bash':
                return MagicMock(returncode=1, stdout="", stderr="expect: command not found")
            
            else:
                return MagicMock(returncode=0, stdout="", stderr="")
        
        with patch('subprocess.run', side_effect=mock_run):
            # Should fall back to local mode
            runner = SmartRecipeRunner(hpc_system='gadi')
            
            # Should have fallen back to local mode
            assert runner.hpc_system == 'local'
            
        print("✅ SSH agent fallback test passed")
        
    finally:
        os.unlink(test_key_path)
        for key in ['GADI_USER', 'GADI_KEY', 'GADI_KEY_PASSPHRASE', 'SCRIPTS_DIR']:
            if key in os.environ:
                del os.environ[key]


if __name__ == '__main__':
    test_ssh_agent_no_expect()
    test_ssh_agent_all_methods_fail()
    print("🎉 All SSH agent scenario tests passed!")
