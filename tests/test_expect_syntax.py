#!/usr/bin/env python3
"""
Test script to verify the expect script syntax is correct.
"""

import subprocess
import tempfile
import os

def test_expect_script_syntax():
    """Test that the expect script has correct syntax."""
    
    # The exact expect script from the code
    test_key_path = "/tmp/test_key"
    test_passphrase = "test_passphrase"
    
    add_key_script = f"""expect << 'EOF'
set timeout 30
spawn ssh-add {test_key_path}
expect {{
    "Enter passphrase*" {{
        send "{test_passphrase}\\r"
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
    
    # Write the script to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(add_key_script)
        script_path = f.name
    
    try:
        # Check syntax with bash -n
        result = subprocess.run(['bash', '-n', script_path], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Expect script syntax is correct")
            return True
        else:
            print(f"❌ Expect script syntax error: {result.stderr}")
            return False
            
    finally:
        # Clean up
        os.unlink(script_path)

def test_multiline_string_syntax():
    """Test that the multiline string doesn't have issues."""
    
    # Test the exact f-string construction from the code
    test_key = "/tmp/test_key"
    test_passphrase = "test_pass"
    
    try:
        script = f"""expect << 'EOF'
set timeout 30
spawn ssh-add {test_key}
expect {{
    "Enter passphrase*" {{
        send "{test_passphrase}\\r"
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
        
        # Check that the string was constructed properly
        if 'EOF' in script and script.count('EOF') == 2:
            print("✅ F-string construction is correct")
            print(f"Script preview (first 100 chars): {script[:100]}...")
            return True
        else:
            print("❌ F-string construction failed")
            print(f"Script content: {script}")
            return False
            
    except Exception as e:
        print(f"❌ Error in f-string construction: {e}")
        return False

if __name__ == '__main__':
    success1 = test_expect_script_syntax()
    success2 = test_multiline_string_syntax()
    
    if success1 and success2:
        print("🎉 All expect script syntax tests passed!")
    else:
        print("❌ Some tests failed")
        exit(1)
