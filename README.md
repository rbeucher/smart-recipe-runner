# Smart Recipe Runner

An intelligent GitHub Action for testing ESMValTool recipes and Jupyter notebooks with adaptive resource management, designed for scientific computing workflows.

## Features

### 🧪 ESMValTool Recipe Testing
- **Automatic recipe fetching** from ESMValTool GitHub repository
- **Branch-specific testing** supporting main, develop, or specific versions
- **Intelligent resource allocation** based on recipe complexity
- **HPC integration** with PBS/SLURM job scheduling
- **Adaptive configuration** with environment detection
- **Comprehensive logging** and error reporting

### 📓 Jupyter Notebook Testing
- **Scientific repository support** (COSIMA Recipes, NCAR, etc.)
- **Automated notebook discovery** with complexity analysis
- **Parallel execution** with resource management
- **Multi-level validation** (syntax, execution, output)
- **Repository-specific configurations** for different scientific domains

### � Cross-Platform Support
- **Local development** environments
- **CI/CD pipelines** (GitHub Actions, GitLab CI)
- **HPC systems** (PBS, SLURM, LSF)
- **Container environments** (Docker, Singularity)

## Installation

### Prerequisites
- Python 3.8 or higher  
- Git
- SSH access to HPC system (for HPC execution)

### For GitHub Actions
Add this action to your workflow file (`.github/workflows/`):

```yaml
name: Test ESMValTool Recipes
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test Recipe
        uses: rbeucher/smart-recipe-runner@main
        with:
          mode: 'recipe'
          recipe_name: 'your_recipe.yml'
```

### Local Development Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/rbeucher/smart-recipe-runner.git
   cd smart-recipe-runner
   ```

2. **Install dependencies:**
   ```bash
   pip install -r lib/requirements.txt
   ```

3. **Configure HPC access (if using HPC execution):**
   ```bash
   export GADI_USER="your_username"
   export GADI_KEY="path/to/ssh/key"
   ```

4. **Run tests:**
   ```bash
   python -m pytest tests/
   ```

### HPC Configuration
For HPC execution, ensure you have:
- SSH key-based authentication configured
- Access to required storage areas and compute queues
- Appropriate conda/module environments available

## Quick Start

### Recipe Testing
```yaml
- name: Test ESMValTool Recipe
  uses: ./smart-recipe-runner
  with:
    mode: 'recipe'
    recipe_name: 'recipe_python.yml'
    config: '{"rootpath": {"default": "/data"}}'
    esmvaltool_version: 'main'

# Test from specific ESMValTool branch
- name: Test Recipe from Development Branch
  uses: ./smart-recipe-runner
  with:
    mode: 'recipe'
    recipe_name: 'recipe_ocean_example.yml'
    esmvaltool_repository: 'https://github.com/ESMValGroup/ESMValTool'
    esmvaltool_branch: 'develop'
    dry_run: true
```

### Notebook Testing
```yaml
- name: Test COSIMA Recipes
  uses: ./smart-recipe-runner
  with:
    mode: 'notebook'
    repository_url: 'https://github.com/COSIMA/cosima-recipes'
    notebook_categories: 'appetisers,tutorials'
    notebook_mode: 'test'
    max_parallel: 3
```

## Input Parameters

### Mode Selection
| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `mode` | Execution mode: `recipe` or `notebook` | No | `recipe` |

### Recipe Parameters
| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `recipe_name` | ESMValTool recipe file name | When mode=recipe | - |
| `esmvaltool_repository` | ESMValTool repository URL | No | `https://github.com/ESMValGroup/ESMValTool` |
| `esmvaltool_branch` | ESMValTool repository branch | No | `main` |
| `config` | Recipe configuration (JSON string or file path) | No | `{}` |
| `esmvaltool_version` | ESMValTool version to use | No | `main` |
| `conda_module` | Conda module name | No | `esmvaltool` |

### Notebook Parameters
| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `repository_url` | Repository URL containing notebooks | When mode=notebook | - |
| `notebook_categories` | Categories to test (comma-separated) | No | `appetisers,tutorials` |
| `notebook_mode` | Test mode: `test`, `validate`, or `dry-run` | No | `test` |
| `max_parallel` | Maximum parallel executions | No | `3` |
| `continue_on_error` | Continue on notebook failures | No | `true` |

### General Parameters
| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `dry_run` | Perform dry run without execution | No | `false` |
| `timeout` | Maximum execution time (seconds) | No | `3600` |

## Notebook Categories

### Supported Repository Types
- **COSIMA Recipes**: `appetisers`, `mains`, `tutorials`, `desserts`, `papers`
- **NCAR Python Tutorial**: `basics`, `meteorology`, `climate`, `visualization`
- **Generic Scientific**: `tutorials`, `examples`, `advanced`, `research`

### Category Descriptions
- **appetisers/basics**: Quick start notebooks (< 5 min execution)
- **mains/tutorials**: Standard tutorials (5-30 min execution)
- **desserts/advanced**: Complex analyses (30+ min execution)
- **papers**: Research paper reproductions (variable execution time)

## Outputs

| Output | Description |
|--------|-------------|
| `status` | Overall execution status (`success`, `partial_failure`, `failure`) |
| `job_id` | PBS/SLURM job ID (if applicable) |
| `report_path` | Path to detailed execution report |
| `summary` | Human-readable execution summary |

## Advanced Usage

### Custom Repository Configuration

For repositories with non-standard structures, create a `.smart-runner.yml` configuration:

```yaml
notebook_testing:
  repository_type: 'custom'
  categories:
    beginner:
      patterns: ['intro-*', 'getting-started/*']
      timeout: 300
      resources: { memory: '2GB', cpu: 1 }
    advanced:
      patterns: ['analysis/*', 'modeling/*']
      timeout: 1800
      resources: { memory: '8GB', cpu: 4 }
  dependencies:
    conda_environment: 'environment.yml'
    pip_requirements: 'requirements.txt'
```

### Matrix Testing

```yaml
strategy:
  matrix:
    repository: 
      - 'https://github.com/COSIMA/cosima-recipes'
      - 'https://github.com/NCAR/python-tutorial'
    categories:
      - 'appetisers,tutorials'
      - 'mains,advanced'
      
steps:
  - name: Test Matrix
    uses: ./smart-recipe-runner
    with:
      mode: 'notebook'
      repository_url: ${{ matrix.repository }}
      notebook_categories: ${{ matrix.categories }}
```

## Architecture

### Notebook Discovery Engine
- **Pattern-based discovery**: Automatically finds notebooks in repository structures
- **Metadata extraction**: Analyzes notebook complexity, dependencies, and requirements
- **Smart categorization**: Classifies notebooks by computational requirements and domain

### Execution Engine
- **Resource allocation**: Dynamically assigns resources based on notebook complexity
- **Parallel processing**: Executes multiple notebooks concurrently with resource limits
- **Timeout management**: Prevents runaway executions with intelligent timeout scaling
- **Error handling**: Comprehensive error capture and reporting

### Reporting System
- **Multi-format outputs**: JSON reports, GitHub annotations, log files
- **Execution metrics**: Runtime, resource usage, success rates
- **Failure analysis**: Detailed error categorization and debugging information

## Directory Structure

```
smart-recipe-runner/
├── action.yml                 # GitHub Action definition
├── lib/
│   ├── recipe-runner.py      # ESMValTool recipe execution
│   ├── config-manager.py     # Configuration management
│   ├── notebook-manager.py   # Notebook discovery and analysis
│   └── notebook-runner.py    # Notebook execution engine
├── docs/
│   ├── architecture.md       # Detailed architecture documentation
│   ├── configuration.md      # Configuration reference
│   └── JUPYTER_NOTEBOOK_TESTING_STRATEGY.md
├── examples/
│   ├── basic-usage.yml       # Simple recipe testing
│   ├── notebook-testing.yml  # Notebook testing examples
│   ├── advanced-usage.yml    # Complex configurations
│   └── matrix-testing.yml    # Matrix strategy examples
└── tests/
    ├── test_recipe_runner.py  # Recipe runner tests
    ├── test_config_manager.py # Configuration tests
    ├── test_notebook_manager.py # Notebook discovery tests
    └── test_notebook_runner.py  # Notebook execution tests
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Test specific components
pytest tests/test_notebook_manager.py -v
pytest tests/test_notebook_runner.py -v

# Run with coverage
pytest tests/ --cov=lib --cov-report=html
```

## Configuration Examples

### COSIMA Recipes Integration
```yaml
- name: Test COSIMA Ocean Analysis
  uses: ./smart-recipe-runner
  with:
    mode: 'notebook'
    repository_url: 'https://github.com/COSIMA/cosima-recipes'
    notebook_categories: 'all'
    notebook_mode: 'test'
    max_parallel: 2
    timeout: 7200  # 2 hours for complex ocean models
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Run the test suite (`pytest tests/ -v`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **ESMValTool Community** for the core recipe framework
- **COSIMA Community** for ocean analysis notebooks and testing insights
- **NCAR** for climate analysis tutorials and best practices
- **Jupyter Project** for the notebook ecosystem
