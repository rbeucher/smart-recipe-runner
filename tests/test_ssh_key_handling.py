#!/usr/bin/env python3
"""
Test SSH key content vs file path handling.
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


def test_ssh_key_content_handling():
    """Test that SSH key content is properly converted to temp file."""
    
    # SSH key content (what GitHub Actions provides)
    ssh_key_content = """-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAACmFlczI1Ni1jdHIAAAAGYmNyeXB0AAAAGAAAABA
test_encrypted_key_content_here
-----END OPENSSH PRIVATE KEY-----"""
    
    try:
        # Set up environment for testing with key content
        os.environ['GADI_USER'] = 'test_user'
        os.environ['GADI_KEY'] = ssh_key_content  # Content, not path
        os.environ['GADI_KEY_PASSPHRASE'] = 'test_passphrase'
        os.environ['SCRIPTS_DIR'] = '/tmp/test_scripts'
        
        # Mock subprocess to simulate successful SSH agent setup
        def mock_run(*args, **kwargs):
            cmd = args[0]
            
            # SSH agent startup
            if cmd == ['ssh-agent', '-s']:
                return MagicMock(
                    returncode=0,
                    stdout="SSH_AUTH_SOCK=/tmp/ssh-agent.123; export SSH_AUTH_SOCK;\nSSH_AGENT_PID=12345; export SSH_AGENT_PID;\n"
                )
            
            # ssh-add with temp file path (should work now)
            elif 'ssh-add' in cmd and len(cmd) == 2:
                key_path = cmd[1]
                print(f"🔧 ssh-add called with: {key_path}")
                
                # Verify it's a temp file path, not content
                if key_path.startswith('/tmp') and 'tmp' in key_path:
                    print("✅ SSH key properly converted to temp file")
                    return MagicMock(returncode=0, stdout="Identity added", stderr="")
                else:
                    print(f"❌ Expected temp file path, got: {key_path}")
                    return MagicMock(returncode=1, stdout="", stderr="Invalid key path")
            
            # Other commands
            else:
                return MagicMock(returncode=0, stdout="", stderr="")
        
        with patch('subprocess.run', side_effect=mock_run):
            runner = SmartRecipeRunner(hpc_system='gadi')
            
            # Check that SSH agent was set up successfully
            assert 'SSH_AUTH_SOCK' in os.environ
            assert 'SSH_AGENT_PID' in os.environ
            
        print("✅ SSH key content handling test passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        # Clean up environment
        for key in ['GADI_USER', 'GADI_KEY', 'GADI_KEY_PASSPHRASE', 'SCRIPTS_DIR', 'SSH_AUTH_SOCK', 'SSH_AGENT_PID']:
            if key in os.environ:
                del os.environ[key]


def test_ssh_key_file_path_handling():
    """Test that SSH key file paths are used directly."""
    
    # Create a temporary key file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
        f.write("""-----BEGIN OPENSSH PRIVATE KEY-----
test_key_content_here
-----END OPENSSH PRIVATE KEY-----""")
        test_key_path = f.name
    
    try:
        # Set up environment for testing with key file path
        os.environ['GADI_USER'] = 'test_user'
        os.environ['GADI_KEY'] = test_key_path  # File path, not content
        os.environ['GADI_KEY_PASSPHRASE'] = 'test_passphrase'
        os.environ['SCRIPTS_DIR'] = '/tmp/test_scripts'
        
        # Mock subprocess
        def mock_run(*args, **kwargs):
            cmd = args[0]
            
            # SSH agent startup
            if cmd == ['ssh-agent', '-s']:
                return MagicMock(
                    returncode=0,
                    stdout="SSH_AUTH_SOCK=/tmp/ssh-agent.123; export SSH_AUTH_SOCK;\nSSH_AGENT_PID=12345; export SSH_AGENT_PID;\n"
                )
            
            # ssh-add with file path (should use original path)
            elif 'ssh-add' in cmd and len(cmd) == 2:
                key_path = cmd[1]
                print(f"🔧 ssh-add called with: {key_path}")
                
                # Verify it's the original file path
                if key_path == test_key_path:
                    print("✅ SSH key file path used directly")
                    return MagicMock(returncode=0, stdout="Identity added", stderr="")
                else:
                    print(f"❌ Expected original path {test_key_path}, got: {key_path}")
                    return MagicMock(returncode=1, stdout="", stderr="Wrong key path")
            
            # Other commands
            else:
                return MagicMock(returncode=0, stdout="", stderr="")
        
        with patch('subprocess.run', side_effect=mock_run):
            runner = SmartRecipeRunner(hpc_system='gadi')
            
            # Check that SSH agent was set up successfully
            assert 'SSH_AUTH_SOCK' in os.environ
            assert 'SSH_AGENT_PID' in os.environ
            
        print("✅ SSH key file path handling test passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        # Clean up
        os.unlink(test_key_path)
        # Clean up environment
        for key in ['GADI_USER', 'GADI_KEY', 'GADI_KEY_PASSPHRASE', 'SCRIPTS_DIR', 'SSH_AUTH_SOCK', 'SSH_AGENT_PID']:
            if key in os.environ:
                del os.environ[key]


if __name__ == '__main__':
    success1 = test_ssh_key_content_handling()
    success2 = test_ssh_key_file_path_handling()
    
    if success1 and success2:
        print("🎉 All SSH key handling tests passed!")
    else:
        print("❌ Some tests failed")
        exit(1)
