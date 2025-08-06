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
            self.scripts_dir = os.environ.get('SCRIPTS_DIR')
            
            if not all([self.gadi_user, self.gadi_key, self.scripts_dir]):
                print("⚠️  Warning: HPC environment variables not set, will run in local mode")
                self.hpc_system = 'local'
        else:
            self.gadi_user = None
            self.gadi_key = None
            self.scripts_dir = None

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
        ssh_cmd = [
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-i', self.gadi_key,
            f'{self.gadi_user}@{self.gadi_host}',
            command
        ]
        
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "SSH command timed out"
        except Exception as e:
            return -1, "", str(e)

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


if __name__ == '__main__':
    main()
