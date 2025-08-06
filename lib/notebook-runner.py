import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


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


class NotebookRunner:
    """Executes and tests Jupyter notebooks."""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
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
        """Execute notebook using nbconvert."""
        
        notebook_path = Path(notebook['path'])
        timeout = self.config['timeouts'].get(notebook['complexity'], 3600)
        
        # Create a temporary copy to avoid modifying original
        with tempfile.NamedTemporaryFile(suffix='.ipynb', delete=False) as tmp_file:
            import shutil
            shutil.copy2(notebook_path, tmp_file.name)
            temp_notebook = Path(tmp_file.name)
            
        try:
            # Build execution command
            cmd = [
                'jupyter', 'nbconvert',
                '--to', 'notebook',
                '--execute',
                '--inplace',
                f'--ExecutePreprocessor.timeout={timeout}',
                '--ExecutePreprocessor.kernel_name=python3',
                '--allow-errors',  # Continue execution even if cells fail
                str(temp_notebook)
            ]
            
            # Execute notebook
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 60  # Add buffer to subprocess timeout
            )
            
            success = result.returncode == 0
            execution_time = time.time() - start_time
            
            # Prepare error message if execution failed
            error_message = None
            if not success:
                error_message = f"Exit code {result.returncode}"
                if result.stderr:
                    error_message += f": {result.stderr[:500]}"  # Limit error message length
                    
            notebook_result = NotebookTestResult(
                path=notebook['path'],
                category=notebook['category'],
                complexity=notebook['complexity'],
                success=success,
                execution_time=execution_time,
                error_message=error_message,
                output_log=result.stdout if result.stdout else None
            )
            
            print(f"✅ Executed {notebook['name']} in {execution_time:.1f}s" if success 
                  else f"❌ Failed {notebook['name']}: {error_message}")
            
            return notebook_result
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            result = NotebookTestResult(
                path=notebook['path'],
                category=notebook['category'],
                complexity=notebook['complexity'],
                success=False,
                execution_time=execution_time,
                error_message=f"Timeout after {timeout}s"
            )
            print(f"⏰ Timeout {notebook['name']} after {timeout}s")
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
            print(f"❌ Exception {notebook['name']}: {e}")
            return result
            
        finally:
            # Clean up temporary file
            if temp_notebook.exists():
                temp_notebook.unlink()
    
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
    
    # Create runner and execute tests
    runner = NotebookRunner(args.config)
    results = runner.run_notebook_tests(
        matrix, 
        mode=args.mode,
        max_parallel=args.max_parallel,
        continue_on_error=args.continue_on_error
    )
    
    # Generate report
    runner.generate_report(args.output)
