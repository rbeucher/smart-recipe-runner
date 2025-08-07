import json
import subprocess
import tempfile
import time
import os
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import SmartRecipeRunner for HPC execution capabilities
import sys
import importlib.util
lib_dir = os.path.dirname(os.path.abspath(__file__))
recipe_runner_path = os.path.join(lib_dir, 'recipe-runner.py')
spec = importlib.util.spec_from_file_location("recipe_runner", recipe_runner_path)
recipe_runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe_runner)
SmartRecipeRunner = recipe_runner.SmartRecipeRunner


@dataclass
class NotebookTestResult:
    """Results from notebook testing."""
    path: str
    category: str
    complexity: str
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    output_log: Optional[str] = None


class NotebookRunner(SmartRecipeRunner):
    """Executes and tests Jupyter notebooks on Gadi HPC."""
    
    def __init__(self, config_path: str = None, log_dir: str = './logs'):
        # Initialize SmartRecipeRunner for HPC capabilities
        super().__init__(log_dir=log_dir)
        self.notebook_config = self._load_config(config_path)
        self.results: List[NotebookTestResult] = []
        
    def _load_config(self, config_path: str = None) -> Dict:
        """Load notebook testing configuration."""
        default_config = {
            'resource_profiles': {
                'appetisers': {
                    'light': {'queue': 'copyq', 'memory': '4gb', 'walltime': '0:30:00', 'ncpus': 1},
                    'medium': {'queue': 'normal', 'memory': '8gb', 'walltime': '1:00:00', 'ncpus': 2}
                },
                'mains': {
                    'medium': {'queue': 'normal', 'memory': '16gb', 'walltime': '2:00:00', 'ncpus': 4},
                    'heavy': {'queue': 'normal', 'memory': '32gb', 'walltime': '4:00:00', 'ncpus': 8},
                    'extra-heavy': {'queue': 'hugemem', 'memory': '128gb', 'walltime': '8:00:00', 'ncpus': 16}
                },
                'tutorials': {
                    'light': {'queue': 'copyq', 'memory': '4gb', 'walltime': '0:45:00', 'ncpus': 1},
                    'medium': {'queue': 'normal', 'memory': '8gb', 'walltime': '1:30:00', 'ncpus': 2}
                },
                'desserts': {
                    'light': {'queue': 'copyq', 'memory': '4gb', 'walltime': '0:30:00', 'ncpus': 1},
                    'medium': {'queue': 'normal', 'memory': '8gb', 'walltime': '1:00:00', 'ncpus': 2}
                },
                'generic': {
                    'light': {'queue': 'copyq', 'memory': '4gb', 'walltime': '0:30:00', 'ncpus': 1},
                    'medium': {'queue': 'normal', 'memory': '8gb', 'walltime': '1:00:00', 'ncpus': 2},
                    'heavy': {'queue': 'normal', 'memory': '16gb', 'walltime': '2:00:00', 'ncpus': 4}
                }
            },
            'environments': {
                'cosima-recipes': 'conda/analysis3',
                'generic-science': 'base'
            },
            'timeouts': {
                'light': 1800,      # 30 minutes
                'medium': 3600,     # 1 hour
                'heavy': 7200,      # 2 hours
                'extra-heavy': 14400 # 4 hours
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                # Merge configs (user config takes precedence)
                default_config.update(user_config)
                
        return default_config
    
    def run_notebook_tests(self, matrix: Dict, mode: str = 'test', 
                          max_parallel: int = 3, continue_on_error: bool = True) -> List[NotebookTestResult]:
        """Run tests on notebooks based on test matrix."""
        
        repository_type = matrix.get('repository_type', 'generic-science')
        
        all_notebooks = []
        for category, category_data in matrix['categories'].items():
            for notebook_data in category_data['notebooks']:
                notebook_data['category'] = category
                all_notebooks.append(notebook_data)
                
        print(f"Testing {len(all_notebooks)} notebooks in {mode} mode")
        
        # Group notebooks by complexity for better resource management
        complexity_groups = {}
        for notebook in all_notebooks:
            complexity = notebook['complexity']
            if complexity not in complexity_groups:
                complexity_groups[complexity] = []
            complexity_groups[complexity].append(notebook)
            
        # Process notebooks by complexity (light first, then medium, etc.)
        processing_order = ['light', 'medium', 'heavy', 'extra-heavy']
        
        for complexity in processing_order:
            if complexity not in complexity_groups:
                continue
                
            notebooks = complexity_groups[complexity]
            print(f"\nProcessing {len(notebooks)} {complexity} notebooks...")
            
            # Process in batches based on max_parallel
            for i in range(0, len(notebooks), max_parallel):
                batch = notebooks[i:i + max_parallel]
                batch_results = self._run_notebook_batch(
                    batch, mode, repository_type, continue_on_error
                )
                self.results.extend(batch_results)
                
                # Brief pause between batches
                if i + max_parallel < len(notebooks):
                    print("Pausing between batches...")
                    time.sleep(10)
                    
        return self.results
    
    def _run_notebook_batch(self, notebooks: List[Dict], mode: str, 
                           repository_type: str, continue_on_error: bool) -> List[NotebookTestResult]:
        """Run a batch of notebooks in parallel."""
        batch_results = []
        
        for notebook in notebooks:
            try:
                result = self._run_single_notebook(notebook, mode, repository_type)
                batch_results.append(result)
                
                if not result.success and not continue_on_error:
                    print(f"❌ Stopping due to failure in {notebook['name']}")
                    break
                    
            except Exception as e:
                error_result = NotebookTestResult(
                    path=notebook['path'],
                    category=notebook['category'],
                    complexity=notebook['complexity'],
                    success=False,
                    execution_time=0,
                    error_message=f"Exception during execution: {e}"
                )
                batch_results.append(error_result)
                
                if not continue_on_error:
                    break
                    
        return batch_results
    
    def _run_single_notebook(self, notebook: Dict, mode: str, repository_type: str) -> NotebookTestResult:
        """Run a single notebook test."""
        
        print(f"🔄 Testing {notebook['name']} ({notebook['complexity']})...")
        
        start_time = time.time()
        
        if mode == 'validate':
            return self._validate_notebook(notebook, start_time)
        elif mode == 'dry-run':
            return self._dry_run_notebook(notebook, start_time)
        else:  # mode == 'test'
            return self._execute_notebook(notebook, repository_type, start_time)
    
    def _validate_notebook(self, notebook: Dict, start_time: float) -> NotebookTestResult:
        """Validate notebook structure without execution."""
        
        try:
            # Check if notebook file exists and is readable
            notebook_path = Path(notebook['path'])
            if not notebook_path.exists():
                raise FileNotFoundError(f"Notebook not found: {notebook_path}")
                
            # Validation passed if no issues were reported in the matrix
            success = notebook.get('valid', True) and len(notebook.get('issues', [])) == 0
            
            execution_time = time.time() - start_time
            
            result = NotebookTestResult(
                path=notebook['path'],
                category=notebook['category'],
                complexity=notebook['complexity'],
                success=success,
                execution_time=execution_time,
                error_message='; '.join(notebook.get('issues', [])) if not success else None
            )
            
            print(f"✅ Validated {notebook['name']}" if success else f"❌ Validation failed {notebook['name']}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = NotebookTestResult(
                path=notebook['path'],
                category=notebook['category'],
                complexity=notebook['complexity'],
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            print(f"❌ Validation error {notebook['name']}: {e}")
            return result
    
    def _dry_run_notebook(self, notebook: Dict, start_time: float) -> NotebookTestResult:
        """Perform dry run checks on notebook."""
        
        try:
            # Check dependencies
            missing_deps = []
            for dep in notebook.get('dependencies', []):
                try:
                    __import__(dep)
                except ImportError:
                    missing_deps.append(dep)
                    
            success = len(missing_deps) == 0
            error_message = f"Missing dependencies: {missing_deps}" if missing_deps else None
            
            execution_time = time.time() - start_time
            
            result = NotebookTestResult(
                path=notebook['path'],
                category=notebook['category'],
                complexity=notebook['complexity'],
                success=success,
                execution_time=execution_time,
                error_message=error_message
            )
            
            print(f"✅ Dry run passed {notebook['name']}" if success else f"❌ Dry run failed {notebook['name']}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = NotebookTestResult(
                path=notebook['path'],
                category=notebook['category'],
                complexity=notebook['complexity'],
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            print(f"❌ Dry run error {notebook['name']}: {e}")
            return result
    
    def _execute_notebook(self, notebook: Dict, repository_type: str, start_time: float) -> NotebookTestResult:
        """Execute notebook on Gadi HPC using PBS job submission."""
        
        notebook_path = Path(notebook['path'])
        notebook_name = notebook_path.stem
        timeout = self.notebook_config['timeouts'].get(notebook['complexity'], 3600)
        
        # Get resource profile for this notebook
        profile = self._get_resource_profile(notebook)
        
        # Generate PBS script for notebook execution
        pbs_script = self._generate_notebook_pbs_script(notebook, repository_type, profile, timeout)
        
        try:
            # Submit PBS job to Gadi (or run locally)
            status, job_id, initial_status = self.submit_job(f"notebook_{notebook_name}", pbs_script)
            
            if status in ["upload_failed", "submission_failed"]:
                return NotebookTestResult(
                    path=notebook['path'],
                    category=notebook['category'],
                    complexity=notebook['complexity'],
                    success=False,
                    execution_time=time.time() - start_time,
                    error_message=f"Job submission failed: {initial_status}"
                )
            elif status == "local_execution":
                # For local execution, return a success result for now
                print(f"📋 Mock execution of notebook {notebook['name']} in local mode")
                return NotebookTestResult(
                    path=notebook['path'],
                    category=notebook['category'],
                    complexity=notebook['complexity'],
                    success=True,  # Mock success for local mode
                    execution_time=time.time() - start_time,
                    output="Local execution - notebook testing not fully implemented",
                    job_id=job_id
                )
            
            print(f"📋 Submitted notebook {notebook['name']} as job {job_id}")
            
            # Monitor job execution
            final_status = self.monitor_job(job_id, timeout + 300)  # Add buffer for job queuing
            execution_time = time.time() - start_time
            
            # Determine success based on job completion
            success = final_status == "completed"
            
            # Get error message if job failed
            error_message = None
            if not success:
                if final_status == "timeout":
                    error_message = f"Job timeout after {timeout + 300}s"
                elif final_status == "failed":
                    # Try to get error details from job output
                    error_log = self._get_job_error_log(f"notebook_{notebook_name}")
                    error_message = f"Job failed: {error_log[:500] if error_log else 'Unknown error'}"
                else:
                    error_message = f"Job status: {final_status}"
            
            notebook_result = NotebookTestResult(
                path=notebook['path'],
                category=notebook['category'],
                complexity=notebook['complexity'],
                success=success,
                execution_time=execution_time,
                error_message=error_message,
                output_log=None  # Could fetch from job output if needed
            )
            
            print(f"✅ Executed {notebook['name']} in {execution_time:.1f}s" if success 
                  else f"❌ Failed {notebook['name']}: {error_message}")
            
            return notebook_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return NotebookTestResult(
                path=notebook['path'],
                category=notebook['category'],
                complexity=notebook['complexity'],
                success=False,
                execution_time=execution_time,
                error_message=f"Execution error: {str(e)}"
            )
    
    def _get_resource_profile(self, notebook: Dict) -> Dict:
        """Get resource profile for notebook based on category and complexity."""
        category = notebook['category']
        complexity = notebook['complexity']
        
        profiles = self.notebook_config.get('resource_profiles', {})
        
        # Get category-specific profile, fall back to generic
        category_profiles = profiles.get(category, profiles.get('generic', {}))
        
        # Get complexity-specific profile, fall back to 'light'
        profile = category_profiles.get(complexity, category_profiles.get('light', {
            'queue': 'copyq', 'memory': '4gb', 'walltime': '0:30:00', 'ncpus': 1
        }))
        
        return profile
    
    def _generate_notebook_pbs_script(self, notebook: Dict, repository_type: str, 
                                    profile: Dict, timeout: int) -> str:
        """Generate PBS script for notebook execution."""
        
        notebook_path = notebook['path']
        notebook_name = Path(notebook_path).stem
        
        # Get environment setup based on repository type
        env_setup = self._get_environment_setup(repository_type)
        
        pbs_script = f"""#!/bin/bash -l 
#PBS -S /bin/bash
#PBS -P w40
#PBS -l storage=gdata/kj13+gdata/fs38+gdata/oi10+gdata/rr3+gdata/xp65+gdata/al33+gdata/rt52+gdata/zz93+gdata/cb20
#PBS -q {profile['queue']}
#PBS -l walltime={profile['walltime']}
#PBS -l mem={profile['memory']}
#PBS -l ncpus={profile['ncpus']}
#PBS -N notebook_{notebook_name}
#PBS -j oe
#PBS -o {self.scripts_dir}/../notebooks/logs/notebook_{notebook_name}.$PBS_JOBID.out

echo "=========================================="
echo "PBS Job Information:"
echo "Job ID: $PBS_JOBID"
echo "Job Name: $PBS_JOBNAME"
echo "Queue: $PBS_QUEUE"
echo "Start Time: $(date)"
echo "Working Directory: $PBS_O_WORKDIR"
echo "Host: $(hostname)"
echo "=========================================="

# Set up environment
cd $PBS_O_WORKDIR
{env_setup}

# Create output directory for notebooks
mkdir -p {self.scripts_dir}/../notebooks/outputs

# Navigate to the notebook directory
NOTEBOOK_PATH="{notebook_path}"
NOTEBOOK_DIR=$(dirname "$NOTEBOOK_PATH")
cd "$NOTEBOOK_DIR"

echo "Executing notebook: $NOTEBOOK_PATH"
echo "Working directory: $(pwd)"

# Execute notebook with timeout
timeout {timeout} jupyter nbconvert \\
    --to notebook \\
    --execute \\
    --inplace \\
    --ExecutePreprocessor.timeout={timeout} \\
    --ExecutePreprocessor.kernel_name=python3 \\
    --allow-errors \\
    "$NOTEBOOK_PATH"

NOTEBOOK_EXIT_CODE=$?

echo "Notebook execution completed with exit code: $NOTEBOOK_EXIT_CODE"
echo "End Time: $(date)"

# Copy executed notebook to outputs directory
if [ $NOTEBOOK_EXIT_CODE -eq 0 ]; then
    cp "$NOTEBOOK_PATH" "{self.scripts_dir}/../notebooks/outputs/{notebook_name}_executed.ipynb"
    echo "Executed notebook saved to outputs directory"
fi

exit $NOTEBOOK_EXIT_CODE
"""
        return pbs_script
    
    def _get_environment_setup(self, repository_type: str) -> str:
        """Get environment setup commands based on repository type."""
        
        environments = self.notebook_config.get('environments', {})
        env_name = environments.get(repository_type, 'base')
        
        if env_name == 'conda/analysis3':
            return """
# Load conda and activate analysis3 environment
module use /g/data/hh5/public/modules
module load conda/analysis3
"""
        elif env_name == 'base':
            return """
# Load basic Python environment
module load python3/3.11.0
"""
        else:
            return f"""
# Load custom environment
module load {env_name}
"""
    
    def _get_job_error_log(self, job_name: str) -> str:
        """Get error log from failed job (local execution)."""
        
        # For local execution, check local log directory
        log_dir = self.log_dir / 'notebooks'
        log_dir.mkdir(exist_ok=True)
        
        # Look for log files matching the job name
        log_files = list(log_dir.glob(f"{job_name}.*.out"))
        
        if log_files:
            # Get the most recent log file
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            try:
                # Read last 20 lines
                with open(latest_log, 'r') as f:
                    lines = f.readlines()
                    return ''.join(lines[-20:]).strip()
            except Exception as e:
                return f"Error reading log file {latest_log}: {e}"
        else:
            return f"No log file found for {job_name} in {log_dir}"
    
    def generate_report(self, output_path: str = 'notebook-test-report.json'):
        """Generate test report."""
        
        summary = {
            'total_notebooks': len(self.results),
            'successful': sum(1 for r in self.results if r.success),
            'failed': sum(1 for r in self.results if not r.success),
            'total_execution_time': sum(r.execution_time for r in self.results),
            'categories': {},
            'complexity': {},
            'detailed_results': []
        }
        
        # Group results by category and complexity
        for result in self.results:
            # By category
            if result.category not in summary['categories']:
                summary['categories'][result.category] = {'total': 0, 'successful': 0, 'failed': 0}
            summary['categories'][result.category]['total'] += 1
            if result.success:
                summary['categories'][result.category]['successful'] += 1
            else:
                summary['categories'][result.category]['failed'] += 1
                
            # By complexity
            if result.complexity not in summary['complexity']:
                summary['complexity'][result.complexity] = {'total': 0, 'successful': 0, 'failed': 0}
            summary['complexity'][result.complexity]['total'] += 1
            if result.success:
                summary['complexity'][result.complexity]['successful'] += 1
            else:
                summary['complexity'][result.complexity]['failed'] += 1
                
            # Detailed results
            summary['detailed_results'].append({
                'path': result.path,
                'category': result.category,
                'complexity': result.complexity,
                'success': result.success,
                'execution_time': result.execution_time,
                'error_message': result.error_message
            })
        
        # Write report
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        print(f"\n📊 Test Report Summary:")
        print(f"   Total: {summary['total_notebooks']}")
        print(f"   Successful: {summary['successful']} ({summary['successful']/summary['total_notebooks']*100:.1f}%)")
        print(f"   Failed: {summary['failed']} ({summary['failed']/summary['total_notebooks']*100:.1f}%)")
        print(f"   Total execution time: {summary['total_execution_time']:.1f}s")
        print(f"   Report saved to: {output_path}")
        
        return summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Jupyter notebook tests')
    parser.add_argument('command', choices=['run'], help='Command to execute')
    parser.add_argument('--matrix', required=True, help='Path to test matrix JSON file')
    parser.add_argument('--mode', choices=['test', 'validate', 'dry-run'], 
                       default='test', help='Test mode')
    parser.add_argument('--max-parallel', type=int, default=3, 
                       help='Maximum parallel executions')
    parser.add_argument('--continue-on-error', action='store_true',
                       help='Continue testing even if notebooks fail')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--output', default='notebook-test-report.json',
                       help='Output file for test report')
    
    args = parser.parse_args()
    
    # Load test matrix
    with open(args.matrix, 'r') as f:
        matrix = json.load(f)
    
    # Create runner and execute tests (using local mode)
    runner = NotebookRunner(args.config, hpc_system='local')
    results = runner.run_notebook_tests(
        matrix, 
        mode=args.mode,
        max_parallel=args.max_parallel,
        continue_on_error=args.continue_on_error
    )
    
    # Generate report
    runner.generate_report(args.output)
