#!/usr/bin/env python3
"""
Smart Recipe Runner for ESMValTool CI/CD

This module handles the execution of ESMValTool recipes on HPC systems,
including PBS job generation, submission, and monitoring.
"""

import argparse
import json
import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional
import time


class SmartRecipeRunner:
    """Intelligent recipe execution manager."""
    
    def __init__(self, gadi_host: str = 'gadi.nci.org.au', hpc_system: str = 'gadi', log_dir: str = './logs', recipe_dir: Optional[str] = None):
        self.gadi_host = gadi_host
        self.hpc_system = hpc_system
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Custom recipe directory for cloned repositories
        self.custom_recipe_dir = recipe_dir
        if recipe_dir:
            self.custom_recipe_dir = Path(recipe_dir)
            print(f"🔗 Using custom recipe directory: {self.custom_recipe_dir}")
        
        # Only set up HPC connection if using HPC system
        if hpc_system == 'gadi':
            self.gadi_user = os.environ.get('GADI_USER')
            self.gadi_key = os.environ.get('GADI_KEY')
            self.gadi_key_passphrase = os.environ.get('GADI_KEY_PASSPHRASE')
            self.scripts_dir = os.environ.get('SCRIPTS_DIR')
            
            if not all([self.gadi_user, self.gadi_key, self.scripts_dir]):
                print("⚠️  Warning: HPC environment variables not set, will run in local mode")
                self.hpc_system = 'local'
            elif self.gadi_key_passphrase:
                print("🔐 Detected password-protected SSH key")
                if not self._setup_ssh_agent():
                    print("⚠️  Warning: Could not setup SSH agent, falling back to local mode")
                    self.hpc_system = 'local'
        else:
            self.gadi_user = None
            self.gadi_key = None
            self.gadi_key_passphrase = None
            self.scripts_dir = None

    def _setup_ssh_agent(self) -> bool:
        """Setup SSH agent with password-protected key."""
        try:
            # Create temporary key file if GADI_KEY contains key content
            key_file_path = self.gadi_key
            temp_key_file = None
            
            # Check if GADI_KEY contains actual key content vs file path
            if self.gadi_key.startswith('-----BEGIN'):
                # GADI_KEY contains the actual key content, create temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
                    f.write(self.gadi_key)
                    temp_key_file = f.name
                    key_file_path = temp_key_file
                os.chmod(temp_key_file, 0o600)  # Set proper permissions
                print("🔧 Created temporary key file from GADI_KEY content")
            else:
                print("🔧 Using GADI_KEY as file path")
            
            try:
                # Start ssh-agent and get environment variables
                result = subprocess.run(['ssh-agent', '-s'], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"❌ Failed to start ssh-agent: {result.stderr}")
                    return False
                
                # Parse SSH_AUTH_SOCK and SSH_AGENT_PID from output
                agent_output = result.stdout
                for line in agent_output.split('\n'):
                    if 'SSH_AUTH_SOCK=' in line:
                        sock_line = line.replace('SSH_AUTH_SOCK=', '').replace('; export SSH_AUTH_SOCK;', '')
                        os.environ['SSH_AUTH_SOCK'] = sock_line
                    elif 'SSH_AGENT_PID=' in line:
                        pid_line = line.replace('SSH_AGENT_PID=', '').replace('; export SSH_AGENT_PID;', '')
                        os.environ['SSH_AGENT_PID'] = pid_line
                
                print(f"🔧 SSH agent started with PID: {os.environ.get('SSH_AGENT_PID', 'unknown')}")
                
                # Method 1: Try using DISPLAY=:0 and SSH_ASKPASS approach
                try:
                    # Create a temporary askpass script
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                        f.write(f"""#!/bin/bash
echo '{self.gadi_key_passphrase}'
""")
                        askpass_script = f.name
                    
                    os.chmod(askpass_script, 0o755)
                    
                    # Set up environment for ssh-add
                    env = os.environ.copy()
                    env['SSH_ASKPASS'] = askpass_script
                    env['DISPLAY'] = ':0'  # Required for SSH_ASKPASS to work
                    env['SSH_ASKPASS_REQUIRE'] = 'force'  # Force use of SSH_ASKPASS
                    
                    result = subprocess.run(['ssh-add', key_file_path], 
                                          capture_output=True, text=True, timeout=30, env=env,
                                          stdin=subprocess.DEVNULL)  # Ensure no stdin interaction
                    os.unlink(askpass_script)
                    
                    if result.returncode == 0:
                        print("✅ Successfully added SSH key to agent (SSH_ASKPASS method)")
                        return True
                    else:
                        print(f"❌ Failed to add key with SSH_ASKPASS: {result.stderr}")
                        
                except Exception as e:
                    print(f"❌ Error with SSH_ASKPASS method: {e}")
                
                # Method 2: Try using sshpass (if available)
                try:
                    # Check if sshpass is available
                    subprocess.run(['which', 'sshpass'], capture_output=True, check=True)
                    
                    result = subprocess.run(['sshpass', '-p', self.gadi_key_passphrase, 'ssh-add', key_file_path], 
                                          capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        print("✅ Successfully added SSH key to agent (sshpass method)")
                        return True
                    else:
                        print(f"❌ Failed to add key with sshpass: {result.stderr}")
                        
                except subprocess.CalledProcessError:
                    print("🔧 sshpass not available, trying alternative methods")
                except Exception as e:
                    print(f"❌ Error with sshpass method: {e}")
                
                # Method 3: Try using expect (if available)
                try:
                    # Check if expect is available
                    subprocess.run(['which', 'expect'], capture_output=True, check=True)
                    
                    add_key_script = f"""expect << 'EOF'
set timeout 30
spawn ssh-add {key_file_path}
expect {{
    "Enter passphrase*" {{
        send "{self.gadi_key_passphrase}\\r"
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
                    
                    result = subprocess.run(['bash', '-c', add_key_script], 
                                          capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        print("✅ Successfully added SSH key to agent (expect method)")
                        return True
                    else:
                        print(f"❌ Failed to add key with expect: {result.stderr}")
                        
                except subprocess.CalledProcessError:
                    print("🔧 expect not available, trying final fallback")
                except Exception as e:
                    print(f"❌ Error with expect method: {e}")
                
                # Method 4: Python-based approach using pexpect (if available)
                try:
                    import pexpect
                    
                    child = pexpect.spawn(f'ssh-add {key_file_path}')
                    child.expect('Enter passphrase.*:')
                    child.sendline(self.gadi_key_passphrase)
                    child.expect(pexpect.EOF, timeout=30)
                    child.close()
                    
                    if child.exitstatus == 0:
                        print("✅ Successfully added SSH key to agent (pexpect method)")
                        return True
                    else:
                        print(f"❌ Failed to add key with pexpect: exit status {child.exitstatus}")
                        
                except ImportError:
                    print("🔧 pexpect not available")
                except Exception as e:
                    print(f"❌ Error with pexpect method: {e}")
                
                # If all methods fail, provide guidance
                print("❌ All SSH agent methods failed. Consider:")
                print("   1. Using a passphrase-free SSH key for CI/CD")
                print("   2. Installing 'expect' or 'sshpass' in your CI environment")
                print("   3. Using GitHub's built-in SSH key support")
                
                return False
                
            finally:
                # Clean up temporary key file if created
                if temp_key_file and os.path.exists(temp_key_file):
                    os.unlink(temp_key_file)
                    print("🧹 Cleaned up temporary key file")
            
        except Exception as e:
            print(f"❌ Error setting up SSH agent: {e}")
            return False

    def check_recent_runs(self, recipe_name: str) -> bool:
        """Check if recipe has run successfully recently."""
        # For now, always run - this could be enhanced with GitHub API calls
        # to check recent workflow runs similar to the original run-recipe action
        return True

    def determine_esmvaltool_path(self, version: str) -> tuple[str, str]:
        """Determine ESMValTool installation path based on version."""
        
        # If using custom recipe directory (cloned repo), use that
        if self.custom_recipe_dir and self.custom_recipe_dir.exists():
            return str(self.custom_recipe_dir.parent.parent), 'esmvaltool/recipes'
        
        # Default version mapping for traditional installations
        version_mapping = {
            'main': ('../ESMValTool-main', 'esmvaltool/recipes'),
            'latest': ('../ESMValTool-main', 'esmvaltool/recipes'),
            'v2.13.0': ('../ESMValTool-2.13', 'esmvaltool/recipes'),
            'v2.12.0': ('../ESMValTool-2.12', 'esmvaltool/recipes'),
            'v2.11.0': ('../ESMValTool-2.11', 'esmvaltool/recipes'),
        }
        
        if version in version_mapping:
            return version_mapping[version]
        elif version.startswith('v2.13'):
            return ('../ESMValTool-2.13', 'esmvaltool/recipes')
        elif version.startswith('v2.12'):
            return ('../ESMValTool-2.12', 'esmvaltool/recipes')
        elif version.startswith('v2.11'):
            return ('../ESMValTool-2.11', 'esmvaltool/recipes')
        else:
            # Custom version/branch
            return (f'../ESMValTool-{version}', 'esmvaltool/recipes')

    def generate_pbs_script(self, recipe_name: str, config: Dict, 
                           esmvaltool_version: str, conda_module: str) -> str:
        """Generate PBS script for recipe execution."""
        
        esmval_path, recipes_path = self.determine_esmvaltool_path(esmvaltool_version)
        
        # Determine config file path based on version
        config_file_version = esmvaltool_version if esmvaltool_version != 'main' else 'main'
        config_file = f"/g/data/kj13/admin/ESMValTool/.esmvaltool/config-user-{config_file_version}.yml"
        fallback_config = "/g/data/kj13/admin/ESMValTool/.esmvaltool/config-user.yml"
        
        # Build max_parallel_tasks parameter if specified
        max_parallel_tasks = config.get('max_parallel_tasks')
        parallel_tasks_param = f" --max_parallel_tasks={max_parallel_tasks}" if max_parallel_tasks else ""
        
        pbs_script = f"""#!/bin/bash -l 
#PBS -S /bin/bash
#PBS -P w40
#PBS -l storage=gdata/kj13+gdata/fs38+gdata/oi10+gdata/rr3+gdata/xp65+gdata/al33+gdata/rt52+gdata/zz93+gdata/cb20
#PBS -N {recipe_name}-{esmvaltool_version}
#PBS -W block=true
#PBS -W umask=037
#PBS -l wd
#PBS -o /g/data/kj13/admin/ESMValTool/logs/{recipe_name}-{esmvaltool_version}.out
#PBS -e /g/data/kj13/admin/ESMValTool/logs/{recipe_name}-{esmvaltool_version}.err
#PBS -q {config['queue']}
#PBS -l walltime={config['walltime']}
#PBS -l mem={config['memory']}

module purge 
module load pbs 

# Load version-specific conda environment
module use /g/data/xp65/public/modules
module load {conda_module}

# Set version-specific config
export ESMVAL_USER_CONFIG={config_file}

# Fall back to main config if version-specific doesn't exist
if [ ! -f "$ESMVAL_USER_CONFIG" ]; then
  export ESMVAL_USER_CONFIG={fallback_config}
fi

# Ensure we're using the correct ESMValTool version
echo "Using ESMValTool version: {esmvaltool_version}"
echo "Config file: $ESMVAL_USER_CONFIG"
echo "Resource group: {config['group']}"
echo "Job started at: $(date)"

# Check if recipe exists for this version
recipe_file="{esmval_path}/{recipes_path}/{recipe_name}.yml"
if [ ! -f "$recipe_file" ]; then
  # Try examples directory
  recipe_file="{esmval_path}/{recipes_path}/examples/{recipe_name}.yml"
fi

if [ ! -f "$recipe_file" ]; then
  echo "ERROR: Recipe {recipe_name}.yml not found for ESMValTool {esmvaltool_version}"
  echo "Searched in:"
  echo "  {esmval_path}/{recipes_path}/{recipe_name}.yml"
  echo "  {esmval_path}/{recipes_path}/examples/{recipe_name}.yml"
  exit 1
fi

echo "Running recipe: $recipe_file"

# Run ESMValTool with version-specific configuration
esmvaltool run --config_file "$ESMVAL_USER_CONFIG" "$recipe_file"{parallel_tasks_param}

echo "Job completed at: $(date)"
"""
        return pbs_script

    def execute_ssh_command(self, command: str, timeout: int = 7200) -> tuple[int, str, str]:
        """Execute command on Gadi via SSH."""
        
        # Determine SSH command based on whether we're using ssh-agent or direct key
        if self.gadi_key_passphrase and 'SSH_AUTH_SOCK' in os.environ:
            # Using ssh-agent - don't specify key file explicitly
            ssh_cmd = [
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'PasswordAuthentication=no',
                '-o', 'PubkeyAuthentication=yes',
                f'{self.gadi_user}@{self.gadi_host}',
                command
            ]
        else:
            # Using key file directly (assumes no passphrase or handled differently)
            ssh_cmd = [
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                '-o', 'PasswordAuthentication=no',
                '-o', 'PubkeyAuthentication=yes',
                '-i', self.gadi_key,
                f'{self.gadi_user}@{self.gadi_host}',
                command
            ]
        
        try:
            # Ensure SSH agent environment is available if using it
            env = os.environ.copy()
            
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "SSH command timed out"
        except Exception as e:
            return -1, "", str(e)

    def cleanup_ssh_agent(self):
        """Clean up SSH agent if it was started."""
        if 'SSH_AGENT_PID' in os.environ:
            try:
                pid = int(os.environ['SSH_AGENT_PID'])
                subprocess.run(['kill', str(pid)], capture_output=True)
                print("🧹 SSH agent cleaned up")
            except (ValueError, subprocess.SubprocessError):
                pass  # Agent might already be dead

    def submit_job(self, recipe_name: str, pbs_script: str) -> tuple[str, str, str]:
        """Submit PBS job to Gadi and return status."""
        
        # Create remote PBS script
        remote_script_path = f"{self.scripts_dir}/../ESMValTool/jobs/launch_{recipe_name}.pbs"
        
        # Create backup of existing script if it exists
        backup_cmd = f"""
        cd {self.scripts_dir}/../ESMValTool/jobs
        if [ -f "launch_{recipe_name}.pbs" ]; then
            cp "launch_{recipe_name}.pbs" "launch_{recipe_name}.pbs.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        """
        
        ret_code, stdout, stderr = self.execute_ssh_command(backup_cmd)
        if ret_code != 0:
            print(f"Warning: Could not create backup: {stderr}")
        
        # Upload PBS script
        upload_cmd = f"""
        cd {self.scripts_dir}/../ESMValTool/jobs
        cat > launch_{recipe_name}.pbs << 'PBSEOF'
{pbs_script}
PBSEOF
        """
        
        ret_code, stdout, stderr = self.execute_ssh_command(upload_cmd)
        if ret_code != 0:
            return "upload_failed", "", f"Failed to upload PBS script: {stderr}"
        
        # Submit job
        submit_cmd = f"""
        cd {self.scripts_dir}/../ESMValTool/jobs
        echo "Submitting PBS job for {recipe_name}..."
        qsub launch_{recipe_name}.pbs 2>&1
        """
        
        ret_code, stdout, stderr = self.execute_ssh_command(submit_cmd, timeout=300)
        
        if ret_code != 0:
            return "submission_failed", "", f"Job submission failed: {stderr}"
        
        # Parse job ID
        job_output = stdout.strip()
        if '.gadi-pbs' in job_output:
            job_id = job_output.split('\n')[-1].strip()
            print(f"Successfully submitted job: {job_id}")
            
            # Check initial status
            time.sleep(5)
            status_cmd = f"qstat -f {job_id} 2>/dev/null | grep job_state | awk '{{print $3}}' || echo 'unknown'"
            _, status_out, _ = self.execute_ssh_command(status_cmd, timeout=30)
            initial_status = status_out.strip() or 'unknown'
            
            return "submitted", job_id, initial_status
        else:
            return "submission_failed", "", f"Could not parse job ID from: {job_output}"

    def find_recipe_file(self, recipe_name: str) -> Optional[str]:
        """Find recipe file in custom directory or default locations."""
        
        # Add .yml extension if not present
        if not recipe_name.endswith('.yml'):
            recipe_name += '.yml'
        
        # Search in custom recipe directory first
        if self.custom_recipe_dir:
            potential_files = [
                self.custom_recipe_dir / recipe_name,
                self.custom_recipe_dir / 'examples' / recipe_name,
                self.custom_recipe_dir / 'testing' / recipe_name,
            ]
            
            for recipe_file in potential_files:
                if recipe_file.exists():
                    print(f"✅ Found recipe: {recipe_file}")
                    return str(recipe_file)
        
        # If no custom directory or file not found, return None
        print(f"❌ Recipe {recipe_name} not found in available directories")
        return None
    
    def run_local(self, recipe_name: str, config_json: str, esmvaltool_version: str, 
                  conda_module: str, mode: str = 'dry-run') -> tuple[str, str]:
        """Run recipe locally (for CI environments)."""
        print(f"🔄 Running recipe '{recipe_name}' locally in {mode} mode")
        
        # Find the recipe file
        recipe_file = self.find_recipe_file(recipe_name)
        if not recipe_file:
            return ('error', '')
        
        print(f"📄 Using recipe file: {recipe_file}")
        
        if mode == 'dry-run':
            print("🧪 Dry-run mode: Would execute ESMValTool with:")
            print(f"   Recipe: {recipe_file}")
            print(f"   Version: {esmvaltool_version}")
            print(f"   Config: {config_json}")
            return ('success', '')
        else:
            print("⚠️  Local execution mode not fully implemented for CI")
            print("   This would require full ESMValTool installation")
            return ('skipped', '')

    def run(self, recipe_name: str, config_json: str, esmvaltool_version: str, 
            conda_module: str, mode: str) -> tuple[str, str]:
        """
        Main execution logic with intelligent mode detection.
        
        Returns:
            (status, job_id)
        """
        
        # For local/CI execution, use local runner
        if self.hpc_system == 'local':
            return self.run_local(recipe_name, config_json, esmvaltool_version, conda_module, mode)
        
        # For HPC execution, use original PBS-based method
        return self.run_hpc(recipe_name, config_json, esmvaltool_version, conda_module, mode)
    
    def run_hpc(self, recipe_name: str, config_json: str, esmvaltool_version: str, 
                conda_module: str, mode: str) -> tuple[str, str]:
        """
        Original HPC execution logic.
        
        Returns:
            (status, job_id)
        """
        
        if mode == 'dry-run':
            print("Dry run mode - would execute recipe but not actually submitting")
            config = json.loads(config_json)
            pbs_script = self.generate_pbs_script(recipe_name, config, esmvaltool_version, conda_module)
            print("Generated PBS script:")
            print("=" * 50)
            print(pbs_script)
            print("=" * 50)
            return "dry-run", ""
        
        # Check if should run (skip recent successful runs)
        if not self.check_recent_runs(recipe_name):
            print(f"Skipping {recipe_name} - ran successfully recently")
            return "skipped", ""
        
        # Parse configuration
        config = json.loads(config_json)
        print(f"Running recipe {recipe_name} with configuration:")
        print(f"  Queue: {config['queue']}")
        print(f"  Memory: {config['memory']}")
        print(f"  Walltime: {config['walltime']}")
        print(f"  Group: {config['group']}")
        
        # Generate PBS script
        pbs_script = self.generate_pbs_script(recipe_name, config, esmvaltool_version, conda_module)
        
        # Submit job
        status, job_id, initial_status = self.submit_job(recipe_name, pbs_script)
        
        if status == "submitted":
            print(f"Job submitted successfully: {job_id}")
            print(f"Initial status: {initial_status}")
            
            # Output for GitHub Actions
            with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
                f.write(f"status={status}\n")
                f.write(f"job_id={job_id}\n") 
                f.write(f"initial_status={initial_status}\n")
                f.write(f"job_submitted=true\n")
            
            return status, job_id
        else:
            print(f"Job submission failed: {status}")
            with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
                f.write(f"status={status}\n")
                f.write(f"job_submitted=false\n")
            return status, ""


def main():
    parser = argparse.ArgumentParser(description='Smart Recipe Runner')
    parser.add_argument('--recipe', required=True, help='Recipe name')
    parser.add_argument('--config', required=True, help='Recipe config as JSON')
    parser.add_argument('--esmvaltool-version', default='main', help='ESMValTool version')
    parser.add_argument('--conda-module', default='conda/access-med', help='Conda module')
    parser.add_argument('--mode', default='run-only', help='Execution mode')
    
    args = parser.parse_args()
    
    runner = None
    try:
        runner = SmartRecipeRunner()
        status, job_id = runner.run(
            recipe_name=args.recipe,
            config_json=args.config,
            esmvaltool_version=args.esmvaltool_version,
            conda_module=args.conda_module,
            mode=args.mode
        )
        
        print(f"Recipe execution completed with status: {status}")
        if job_id:
            print(f"Job ID: {job_id}")
            
    except Exception as e:
        print(f"Error in recipe execution: {e}")
        with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
            f.write(f"status=error\n")
            f.write(f"job_submitted=false\n")
        sys.exit(1)
    finally:
        # Clean up SSH agent if it was started
        if runner:
            runner.cleanup_ssh_agent()


if __name__ == '__main__':
    main()
