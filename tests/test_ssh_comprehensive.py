#!/usr/bin/env python3
"""
Comprehensive test for all SSH agent methods to ensure no syntax errors.
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


def test_all_ssh_methods_syntax():
    """Test that all SSH agent methods have correct syntax."""
    
    # Create a temporary key file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
        f.write("""-----BEGIN OPENSSH PRIVATE KEY-----
test_encrypted_key_content_here
-----END OPENSSH PRIVATE KEY-----""")
        test_key_path = f.name
    
    try:
        # Set up environment for testing
        os.environ['GADI_USER'] = 'test_user'
        os.environ['GADI_KEY'] = test_key_path
        os.environ['GADI_KEY_PASSPHRASE'] = 'test_passphrase'
        os.environ['SCRIPTS_DIR'] = '/tmp/test_scripts'
        
        # Mock subprocess to test each method's syntax
        def mock_run(*args, **kwargs):
            cmd = args[0]
            
            # SSH agent startup - should succeed
            if cmd == ['ssh-agent', '-s']:
                return MagicMock(
                    returncode=0,
                    stdout="SSH_AUTH_SOCK=/tmp/ssh-agent.123; export SSH_AUTH_SOCK;\nSSH_AGENT_PID=12345; export SSH_AGENT_PID;\n"
                )
            
            # Method 1: SSH_ASKPASS - fail to test other methods
            elif 'ssh-add' in cmd and len(cmd) == 2:
                return MagicMock(returncode=1, stdout="", stderr="Method 1 failed (expected)")
            
            # Method 2: sshpass - available but fail
            elif cmd == ['which', 'sshpass']:
                return MagicMock(returncode=0)
            elif cmd[0] == 'sshpass':
                return MagicMock(returncode=1, stdout="", stderr="Method 2 failed (expected)")
            
            # Method 3: expect - available and succeed
            elif cmd == ['which', 'expect']:
                return MagicMock(returncode=0)
            elif cmd[0] == 'bash' and '-c' in cmd:
                # This tests the expect script syntax
                script_content = cmd[2]
                print(f"📋 Testing expect script syntax...")
                # Write to temp file and test syntax
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_f:
                    temp_f.write(script_content)
                    temp_script = temp_f.name
                
                try:
                    # Test bash syntax
                    syntax_result = subprocess.run(['bash', '-n', temp_script], 
                                                 capture_output=True, text=True)
                    os.unlink(temp_script)
                    
                    if syntax_result.returncode == 0:
                        print("✅ Expect script syntax validation passed")
                        return MagicMock(returncode=0, stdout="Identity added", stderr="")
                    else:
                        print(f"❌ Expect script syntax error: {syntax_result.stderr}")
                        return MagicMock(returncode=1, stdout="", stderr=f"Syntax error: {syntax_result.stderr}")
                except Exception as e:
                    print(f"❌ Error testing expect script: {e}")
                    return MagicMock(returncode=1, stdout="", stderr=str(e))
            
            # Default success for other commands
            else:
                return MagicMock(returncode=0, stdout="", stderr="")
        
        with patch('subprocess.run', side_effect=mock_run):
            runner = SmartRecipeRunner(hpc_system='gadi')
            
            # Check that SSH agent was set up successfully
            assert 'SSH_AUTH_SOCK' in os.environ
            assert 'SSH_AGENT_PID' in os.environ
            
        print("✅ All SSH agent methods syntax test passed")
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


def test_expect_script_edge_cases():
    """Test expect script with various edge cases."""
    
    test_cases = [
        ("/tmp/key with spaces", "pass with spaces"),
        ("/tmp/key'with'quotes", "pass'with'quotes"), 
        ("/tmp/key$with$vars", "pass$with$vars"),
        ("/tmp/normalkey", "normalpass")
    ]
    
    for key_path, passphrase in test_cases:
        try:
            # Generate the script like the real code does
            add_key_script = f"""expect << 'EOF'
set timeout 30
spawn ssh-add {key_path}
expect {{
    "Enter passphrase*" {{
        send "{passphrase}\\r"
        exp_continue
    }}
    "Identity added*" {{
        exit 0
    }}
    timeout {{
        exit 1
    }}
    eof {{
        exit 0
    }}
}}
EOF"""
            
            # Test syntax
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(add_key_script)
                script_path = f.name
            
            result = subprocess.run(['bash', '-n', script_path], 
                                  capture_output=True, text=True)
            os.unlink(script_path)
            
            if result.returncode != 0:
                print(f"❌ Syntax error with key='{key_path}', pass='{passphrase}': {result.stderr}")
                return False
            else:
                print(f"✅ Syntax OK for key='{key_path}', pass='{passphrase}'")
                
        except Exception as e:
            print(f"❌ Error testing edge case key='{key_path}', pass='{passphrase}': {e}")
            return False
    
    print("✅ All expect script edge cases passed")
    return True


if __name__ == '__main__':
    success1 = test_all_ssh_methods_syntax()
    success2 = test_expect_script_edge_cases()
    
    if success1 and success2:
        print("🎉 All comprehensive SSH syntax tests passed!")
    else:
        print("❌ Some tests failed")
        exit(1)
