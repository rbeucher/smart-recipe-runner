# Smart Recipe Runner

[![Tests](https://github.com/rbeucher/smart-recipe-runner/workflows/Test%20Smart%20Recipe%20Runner/badge.svg)](https://github.com/rbeucher/smart-recipe-runner/actions/workflows/test.yml)

An intelligent GitHub Action for executing ESMValTool and COSIMA recipes with adaptive resource management on HPC systems.

## Features

### 🧪 ESMValTool Recipe Execution
- **PBS script generation** for HPC job submission
- **Version-specific support** for ESMValTool (main, latest, specific versions)
- **Intelligent resource allocation** based on recipe complexity
- **Automatic repository cloning** and environment setup

### 📓 COSIMA Recipe Support
- **Jupyter notebook execution** for ocean analysis workflows
- **COSIMA-specific PBS configurations** optimized for ocean modeling
- **Repository integration** with automatic dependency management

### 🏗️ Simple Architecture
- **Single core component**: Recipe Runner for PBS script generation  
- **Simplified workflow**: Generate PBS script → Submit via ssh-action
- **Intelligent defaults**: Automatic resource allocation based on recipe type
- **No complex HPC integration**: Relies on ssh-action for job submission

## Installation

### Prerequisites
- Python 3.8 or higher  
- Git
- SSH access to HPC system (configured via ssh-action)

### For GitHub Actions
Add this action to your workflow file (`.github/workflows/`):

```yaml
name: Test ESMValTool Recipes
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
```yaml
name: Test ESMValTool Recipe
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Test Recipe
        uses: rbeucher/smart-recipe-runner@main
        with:
          recipe_type: 'esmvaltool'
          recipe_name: 'recipe_python.yml'
          config: '{"rootpath": {"default": "/data"}}'
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

3. **Run tests:**
   ```bash
   python -m pytest tests/
   ```

## Quick Start

### ESMValTool Recipe
```yaml
- name: Test ESMValTool Recipe
  uses: rbeucher/smart-recipe-runner@main
  with:
    recipe_type: 'esmvaltool'
    recipe_name: 'recipe_python.yml'
    config: '{"rootpath": {"default": "/data"}}'
    esmvaltool_version: 'main'
```

### COSIMA Recipe
```yaml
- name: Test COSIMA Recipe
  uses: rbeucher/smart-recipe-runner@main
  with:
    recipe_type: 'cosima'
    recipe_name: 'ocean_analysis'
    repository_url: 'https://github.com/COSIMA/cosima-recipes'
```

## Input Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `recipe_type` | Recipe type: `esmvaltool` or `cosima` | Yes | - |
| `recipe_name` | Recipe file name or notebook name | Yes | - |
| `config` | Configuration (JSON string) | No | `{}` |
| `esmvaltool_version` | ESMValTool version (for esmvaltool recipes) | No | `main` |
| `conda_module` | Conda module to load | No | `conda/access-med` |
| `repository_url` | Repository URL (for cloning custom repos) | No | - |

## Outputs

| Output | Description |
|--------|-------------|
| `status` | Execution status (`pbs-generated`) |
| `pbs_filename` | Generated PBS script filename |

## Advanced Usage

### Matrix Testing
```yaml
strategy:
  matrix:
    recipe_type: ['esmvaltool', 'cosima']
    recipe: 
      - 'recipe_python.yml'
      - 'recipe_ocean_example.yml'
      
steps:
  - name: Test Matrix
    uses: rbeucher/smart-recipe-runner@main
    with:
      recipe_type: ${{ matrix.recipe_type }}
      recipe_name: ${{ matrix.recipe }}
```

### Custom Repository Testing
```yaml
- name: Test Custom Repository
  uses: rbeucher/smart-recipe-runner@main
  with:
    recipe_type: 'esmvaltool'
    recipe_name: 'my_custom_recipe.yml'
    repository_url: 'https://github.com/myorg/my-esmvaltool-recipes'
```

## Architecture

The Smart Recipe Runner uses a simple single-component architecture:

### Recipe Runner (`lib/recipe-runner.py`)
- **PBS script generation**: Creates HPC-optimized job scripts with intelligent defaults
- **Multi-platform support**: ESMValTool and COSIMA recipe execution
- **Automatic resource allocation**: Maps recipe types to appropriate PBS configurations
- **Environment setup**: Handles conda environments and repository cloning
- **Output management**: Provides structured outputs for ssh-action integration

### Execution Flow
1. **Configuration Analysis**: Analyze recipe requirements and generate resource configuration
2. **PBS Script Generation**: Create optimized PBS script with proper resource allocation
3. **Output Delivery**: Provide PBS script for ssh-action to upload and submit

## Directory Structure

```
smart-recipe-runner/
├── action.yml                 # GitHub Action definition
├── lib/
│   ├── recipe-runner.py      # PBS script generation with intelligent defaults
│   └── requirements.txt      # Python dependencies
├── docs/
│   ├── architecture.md       # Architecture documentation
│   ├── configuration.md      # Configuration reference
│   └── troubleshooting.md    # Troubleshooting guide
├── examples/
│   ├── basic-usage.yml       # Simple recipe testing
│   ├── advanced-usage.yml    # Complex configurations
│   ├── cosima-usage.yml      # COSIMA workflow examples
│   └── matrix-testing.yml    # Matrix strategy examples
└── tests/
    ├── test_recipe_runner.py  # Recipe runner tests
    └── test_config_manager.py # Configuration tests
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Test specific components
pytest tests/test_config_manager.py -v
pytest tests/test_recipe_runner.py -v

# Run with coverage
pytest tests/ --cov=lib --cov-report=html
```

## Configuration Examples

### Complete ESMValTool Workflow
```yaml
name: ESMValTool Recipe Testing
on: [push, pull_request]

jobs:
  test-recipe:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate PBS Script
        id: pbs
        uses: rbeucher/smart-recipe-runner@main
        with:
          recipe_type: 'esmvaltool'
          recipe_name: 'recipe_python.yml'
          esmvaltool_version: 'main'
          config: '{"rootpath": {"default": "/g/data/ks32/ESMValTool"}}'
      
      - name: Submit to HPC
        uses: ACCESS-NRI/ssh-action@v1
        with:
          host: 'gadi.nci.org.au'
          username: ${{ secrets.GADI_USERNAME }}
          key: ${{ secrets.GADI_SSH_KEY }}
          script: |
            cd /scratch/$USER/scripts
            qsub ${{ steps.pbs.outputs.pbs_filename }}
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
- **COSIMA Community** for ocean analysis workflows and testing insights
- **ACCESS-NRI** for HPC integration and ssh-action support
