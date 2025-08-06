import nbformat
import json
from pathlib import Path
from typing import Dict, List, Tuple
import ast
import re


class NotebookManager:
    """Manages discovery and analysis of Jupyter notebooks in scientific repositories."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repository_type = self._detect_repository_type()
        
    def _detect_repository_type(self) -> str:
        """Auto-detect repository type based on structure."""
        if (self.repo_path / 'Recipes').exists() and (self.repo_path / 'Cooking-Lessons-101-Tutorials').exists():
            return 'cosima-recipes'
        elif (self.repo_path / 'notebooks').exists():
            return 'generic-science'
        else:
            return 'unknown'
    
    def discover_notebooks(self, categories: List[str] = None) -> Dict[str, List[Path]]:
        """Discover and categorize notebooks by directory structure."""
        all_categories = {
            'appetisers': [],      # Quick, lightweight notebooks
            'mains': [],           # Full analysis notebooks  
            'desserts': [],        # Plotting/visualization
            'tutorials': [],       # Educational content
            'papers': [],          # Paper reproduction
            'generic': []          # Uncategorized notebooks
        }
        
        # Define search patterns based on repository type
        if self.repository_type == 'cosima-recipes':
            search_dirs = ['Recipes', 'Cooking-Lessons-101-Tutorials', 'ACCESS-OM2-GMD-Paper-Figs']
        else:
            search_dirs = ['notebooks', 'examples', 'tutorials', '.']
            
        # Search for .ipynb files
        for search_dir in search_dirs:
            search_path = self.repo_path / search_dir
            if search_path.exists():
                for notebook_path in search_path.rglob('*.ipynb'):
                    # Skip checkpoint files
                    if '.ipynb_checkpoints' in str(notebook_path):
                        continue
                        
                    category = self._classify_notebook(notebook_path)
                    all_categories[category].append(notebook_path)
        
        # Filter by requested categories if specified
        if categories:
            if 'all' in categories:
                return all_categories
            else:
                return {cat: notebooks for cat, notebooks in all_categories.items() 
                       if cat in categories}
        
        return all_categories
    
    def _classify_notebook(self, notebook_path: Path) -> str:
        """Classify notebook based on path and content analysis."""
        path_str = str(notebook_path).lower()
        
        # COSIMA-specific classification
        if self.repository_type == 'cosima-recipes':
            if 'appetiser' in path_str or 'easy' in path_str:
                return 'appetisers'
            elif 'main' in path_str or 'advanced' in path_str:
                return 'mains'
            elif 'dessert' in path_str or 'plotting' in path_str:
                return 'desserts'
            elif 'tutorial' in path_str or 'lesson' in path_str:
                return 'tutorials'
            elif 'paper' in path_str or 'fig' in path_str:
                return 'papers'
        
        # Generic classification
        if 'tutorial' in path_str or 'example' in path_str:
            return 'tutorials'
        elif 'plot' in path_str or 'viz' in path_str:
            return 'desserts'
        elif 'advanced' in path_str or 'complex' in path_str:
            return 'mains'
        else:
            return 'generic'
    
    def analyze_notebook_complexity(self, notebook_path: Path) -> str:
        """Analyze notebook computational requirements."""
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = nbformat.read(f, as_version=4)
                
            complexity_indicators = {
                'extra-heavy': [
                    'dask.distributed', 'Client()', 'cluster =', 'LocalCluster',
                    'from dask', 'dask.array', 'dask.dataframe'
                ],
                'heavy': [
                    'xarray.open_mfdataset', 'intake.cat', 'large dataset',
                    'parallel', 'multiprocessing', 'concurrent.futures'
                ],
                'medium': [
                    'xarray', 'pandas', 'numpy.load', 'intake',
                    'netcdf', 'hdf5', 'zarr'
                ],
                'light': [
                    'matplotlib', 'pyplot', 'seaborn', 'plotly',
                    'simple', 'basic'
                ]
            }
            
            cell_count = len([c for c in notebook.cells if c.cell_type == 'code'])
            code_content = ' '.join([
                cell.source for cell in notebook.cells 
                if cell.cell_type == 'code'
            ])
            
            # Check for computational indicators (in order of heaviness)
            for complexity, indicators in complexity_indicators.items():
                if any(indicator in code_content for indicator in indicators):
                    # Adjust based on cell count
                    if complexity == 'light' and cell_count > 20:
                        return 'medium'
                    elif complexity == 'medium' and cell_count > 30:
                        return 'heavy'
                    elif complexity == 'heavy' and cell_count > 40:
                        return 'extra-heavy'
                    return complexity
                    
            # Fallback based on cell count only
            if cell_count > 40:
                return 'heavy'
            elif cell_count > 20:
                return 'medium'
            else:
                return 'light'
                
        except Exception as e:
            print(f"Error analyzing {notebook_path}: {e}")
            return 'medium'  # Safe default
    
    def validate_notebook_structure(self, notebook_path: Path) -> Tuple[bool, List[str]]:
        """Validate notebook structure and syntax."""
        issues = []
        
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = nbformat.read(f, as_version=4)
                
            # Check basic structure
            if not notebook.cells:
                issues.append("Notebook has no cells")
                return False, issues
                
            code_cells = [c for c in notebook.cells if c.cell_type == 'code']
            if not code_cells:
                issues.append("Notebook has no code cells")
                
            # Check for syntax errors in first few cells
            for i, cell in enumerate(code_cells[:5]):
                if cell.source.strip():  # Skip empty cells
                    try:
                        ast.parse(cell.source)
                    except SyntaxError as e:
                        issues.append(f"Syntax error in cell {i+1}: {e}")
                        
            # Check for common issues
            full_content = ' '.join([c.source for c in code_cells])
            
            # Check for hardcoded paths (potential issue)
            if re.search(r'/home/\w+', full_content) or re.search(r'C:\\Users', full_content):
                issues.append("Contains hardcoded user paths")
                
            # Check for missing docstrings in complex notebooks
            if len(code_cells) > 10:
                markdown_cells = [c for c in notebook.cells if c.cell_type == 'markdown']
                if len(markdown_cells) < 3:
                    issues.append("Complex notebook with minimal documentation")
                    
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Failed to read notebook: {e}")
            return False, issues
    
    def get_notebook_dependencies(self, notebook_path: Path) -> List[str]:
        """Extract dependencies from notebook imports."""
        dependencies = set()
        
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = nbformat.read(f, as_version=4)
                
            for cell in notebook.cells:
                if cell.cell_type == 'code':
                    # Extract import statements
                    lines = cell.source.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith('import '):
                            module = line.replace('import ', '').split()[0]
                            dependencies.add(module.split('.')[0])
                        elif line.startswith('from '):
                            match = re.match(r'from\s+(\w+)', line)
                            if match:
                                dependencies.add(match.group(1))
                                
        except Exception as e:
            print(f"Error extracting dependencies from {notebook_path}: {e}")
            
        return sorted(list(dependencies))
    
    def generate_test_matrix(self, categories: List[str] = None) -> Dict:
        """Generate test matrix for CI/CD."""
        notebooks = self.discover_notebooks(categories)
        
        matrix = {
            'repository_type': self.repository_type,
            'total_notebooks': sum(len(nb_list) for nb_list in notebooks.values()),
            'categories': {}
        }
        
        for category, notebook_list in notebooks.items():
            if not notebook_list:
                continue
                
            category_data = {
                'count': len(notebook_list),
                'notebooks': []
            }
            
            for notebook_path in notebook_list:
                complexity = self.analyze_notebook_complexity(notebook_path)
                is_valid, issues = self.validate_notebook_structure(notebook_path)
                dependencies = self.get_notebook_dependencies(notebook_path)
                
                notebook_data = {
                    'path': str(notebook_path.relative_to(self.repo_path)),
                    'name': notebook_path.stem,
                    'complexity': complexity,
                    'valid': is_valid,
                    'issues': issues,
                    'dependencies': dependencies,
                    'estimated_runtime': self._estimate_runtime(complexity)
                }
                
                category_data['notebooks'].append(notebook_data)
                
            matrix['categories'][category] = category_data
            
        return matrix
    
    def _estimate_runtime(self, complexity: str) -> int:
        """Estimate runtime in minutes based on complexity."""
        runtime_map = {
            'light': 5,
            'medium': 15,
            'heavy': 45,
            'extra-heavy': 120
        }
        return runtime_map.get(complexity, 15)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage Jupyter notebooks in scientific repositories')
    parser.add_argument('command', choices=['discover', 'analyze', 'validate'], 
                       help='Command to execute')
    parser.add_argument('--repo-path', required=True, help='Path to repository')
    parser.add_argument('--categories', help='Comma-separated list of categories')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    manager = NotebookManager(args.repo_path)
    categories = args.categories.split(',') if args.categories else None
    
    if args.command == 'discover':
        notebooks = manager.discover_notebooks(categories)
        result = {cat: [str(nb) for nb in nb_list] for cat, nb_list in notebooks.items()}
        
    elif args.command == 'analyze':
        result = manager.generate_test_matrix(categories)
        
    elif args.command == 'validate':
        notebooks = manager.discover_notebooks(categories)
        result = {'validation_results': {}}
        
        for category, notebook_list in notebooks.items():
            result['validation_results'][category] = []
            for notebook_path in notebook_list:
                is_valid, issues = manager.validate_notebook_structure(notebook_path)
                result['validation_results'][category].append({
                    'path': str(notebook_path),
                    'valid': is_valid,
                    'issues': issues
                })
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))
