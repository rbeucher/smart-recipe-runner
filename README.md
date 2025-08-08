# Smart Recipe Runner

[![Tests](https://github.com/rbeucher/smart-recipe-runner/workflows/Test%20Smart%20Recipe%20Runner/badge.svg)](https://github.com/rbeucher/smart-recipe-runner/actions/workflows/test.yml)

An intelligent GitHub Action for executing ESMValTool and COSIMA recipes with adaptive resource management on HPC systems.

## Features

### 🧪 ESMValTool Recipe Execution
- **PBS script generation** for HPC job submission
- **Version-specific support** for ESMValTool (main, latest, specific versions)
- **Intelligent resource allocation** based on recipe complexity
- **Automatic repository cloning** - pulls ESMValTool repository on Gadi and uses recipes from there
- **Comprehensive recipe search** - searches multiple locations within the repository
- **Error handling and diagnostics** - lists available recipes if target recipe not found

### 📓 COSIMA Recipe Support
- **Jupyter notebook and Python script execution** for ocean analysis workflows
- **COSIMA-specific PBS configurations** optimized for ocean modeling
- **Automatic repository cloning** - pulls COSIMA recipes repository on Gadi
- **Flexible recipe formats** - supports .py and .ipynb files
- **Multiple search locations** - searches notebooks/, scripts/, examples/ directories

### 🏗️ Simple & Complete Architecture
- **Single core component**: Recipe Runner for PBS script generation  
- **Two execution modes**: 
  - **Generate-only**: Create PBS script with pre-cloned repository references
  - **Full execution**: Clone repositories on Gadi → Generate PBS script → Submit job
- **Internet-safe design**: Repository cloning happens on login nodes (with internet), jobs run on compute nodes (without internet)
- **Intelligent defaults**: Automatic resource allocation based on recipe type
- **Built-in HPC integration**: Direct SSH connection and job submission to Gadi

## Installation

### Prerequisites
- Python 3.8 or higher  
- Git
- For job submission: SSH access to Gadi HPC system

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

### ESMValTool Recipe (Generate PBS only)
```yaml
- name: Generate PBS Script
  uses: rbeucher/smart-recipe-runner@main
  with:
    recipe_type: 'esmvaltool'
    recipe_name: 'recipe_python.yml'
    config: '{"rootpath": {"default": "/data"}}'
    esmvaltool_version: 'main'
```

### ESMValTool Recipe (Generate and Submit to Gadi)
```yaml
### ESMValTool Recipe (Generate and Submit to Gadi)
```yaml
- name: Run ESMValTool Recipe on Gadi
  uses: rbeucher/smart-recipe-runner@main
  with:
    recipe_type: 'esmvaltool'
    recipe_name: 'recipe_python.yml'
    config: '{"rootpath": {"default": "/g/data/ks32/ESMValTool"}}'
    esmvaltool_version: 'main'
    project: 'kj13'  # Specify your PBS project
    submit_job: 'true'
    gadi_username: ${{ secrets.GADI_USERNAME }}
    gadi_ssh_key: ${{ secrets.GADI_SSH_KEY }}
    # Optional: Add if SSH key is password-protected
    gadi_ssh_passphrase: ${{ secrets.GADI_SSH_PASSPHRASE }}
```

### COSIMA Recipe
```yaml
- name: Run COSIMA Recipe on Gadi
  uses: rbeucher/smart-recipe-runner@main
  with:
    recipe_type: 'cosima'
    recipe_name: 'ocean_analysis'
    repository_url: 'https://github.com/COSIMA/cosima-recipes'
    submit_job: 'true'
    gadi_username: ${{ secrets.GADI_USERNAME }}
    gadi_ssh_key: ${{ secrets.GADI_SSH_KEY }}
    # Optional: Add if SSH key is password-protected
    gadi_ssh_passphrase: ${{ secrets.GADI_SSH_PASSPHRASE }}
```
  with:
    recipe_type: 'cosima'
    recipe_name: 'ocean_analysis'
    repository_url: 'https://github.com/COSIMA/cosima-recipes'
    submit_job: 'true'
    gadi_username: ${{ secrets.GADI_USERNAME }}
    gadi_ssh_key: ${{ secrets.GADI_SSH_KEY }}
```

### Recipe Repository Handling

The action automatically handles repository cloning and recipe discovery on Gadi:

**Repository Cloning Strategy:**
- **Login node cloning**: Repositories are cloned/updated on Gadi login nodes (which have internet access)
- **Compute node execution**: PBS jobs run on compute nodes using pre-cloned repositories (no internet needed)
- **This design ensures compatibility with all PBS queues**, even those without internet access

**For ESMValTool recipes:**
- Clones/updates the ESMValTool repository to `ESMValTool-ci/` on Gadi login node
- PBS script uses pre-cloned repository at `/scratch/$USER/../ESMValTool-ci/`
- Searches for recipes in multiple locations:
  - `esmvaltool/recipes/{recipe_name}.yml`
  - `esmvaltool/recipes/examples/{recipe_name}.yml`
  - `esmvaltool/recipes/*/{recipe_name}.yml`
- Lists available recipes if the specified recipe is not found

**For COSIMA recipes:**
- Clones/updates the COSIMA recipes repository to `COSIMA-recipes-ci/` on Gadi login node
- PBS script uses pre-cloned repository at `/scratch/$USER/../COSIMA-recipes-ci/`
- Searches for recipes in multiple locations and formats:
  - Root directory: `{recipe_name}`, `{recipe_name}.py`, `{recipe_name}.ipynb`
  - `notebooks/` directory: `{recipe_name}`, `{recipe_name}.py`, `{recipe_name}.ipynb`
  - `scripts/` and `examples/` directories
- Supports both Python scripts (`.py`) and Jupyter notebooks (`.ipynb`)

## Input Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `recipe_type` | Recipe type: `esmvaltool` or `cosima` | Yes | - |
| `recipe_name` | Recipe file name or notebook name | Yes | - |
| `config` | Configuration (JSON string) | No | `{}` |
| `esmvaltool_version` | ESMValTool version (for esmvaltool recipes) | No | `main` |
| `conda_module` | Conda module to load | No | `conda/analysis3` |
| `project` | PBS project code (e.g., w40, kj13, etc.) | No | `w40` |
| `repository_url` | Repository URL (for cloning custom repos) | No | - |
| `submit_job` | Submit job to Gadi (`true`/`false`) | No | `false` |
| `gadi_username` | Gadi username for SSH connection | No | - |
| `gadi_ssh_key` | SSH private key for Gadi | No | - |
| `gadi_ssh_passphrase` | Passphrase for SSH private key (if password-protected) | No | - |
| `scripts_dir` | Directory on Gadi for scripts | No | `/scratch/$USER/esmvaltool-ci` |

## Outputs

| Output | Description |
|--------|-------------|
| `status` | Execution status (`pbs-generated`, `job-submitted`, or `error`) |
| `pbs_filename` | Generated PBS script filename |
| `job_id` | PBS job ID (if submitted - check SSH output) | 
| `gadi_path` | Path to script on Gadi (if submitted) |

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
- **PBS script generation**: Creates HPC-optimized job scripts that reference pre-cloned repositories
- **Multi-platform support**: ESMValTool and COSIMA recipe execution
- **Automatic resource allocation**: Maps recipe types to appropriate PBS configurations
- **Internet-safe design**: PBS scripts expect repositories to be pre-cloned on login nodes
- **SSH integration**: Handles repository cloning on login nodes and job submission to compute nodes
- **Output management**: Provides job IDs and monitoring information

### Execution Flow
1. **Configuration Analysis**: Analyze recipe requirements and generate resource configuration
2. **PBS Script Generation**: Create optimized PBS script that references pre-cloned repositories
3. **Repository Setup** (if submitting): SSH to Gadi login node and clone/update repositories (with internet access)
4. **Job Submission** (if submitting): Upload PBS script and submit to compute nodes (no internet needed)
5. **Output Delivery**: Provide job ID and monitoring information

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

### Complete ESMValTool Workflow (Generate + Submit)
```yaml
name: ESMValTool Recipe Execution
on: [push, pull_request]

jobs:
  run-recipe:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run ESMValTool Recipe on Gadi
        id: recipe
        uses: rbeucher/smart-recipe-runner@main
        with:
          recipe_type: 'esmvaltool'
          recipe_name: 'recipe_python.yml'
          esmvaltool_version: 'main'
          config: '{"rootpath": {"default": "/g/data/ks32/ESMValTool"}}'
          submit_job: 'true'
          gadi_username: ${{ secrets.GADI_USERNAME }}
          gadi_ssh_key: ${{ secrets.GADI_SSH_KEY }}
          # Optional: Add if SSH key is password-protected
          gadi_ssh_passphrase: ${{ secrets.GADI_SSH_PASSPHRASE }}
      
      - name: Show Results
        run: |
          echo "Status: ${{ steps.recipe.outputs.status }}"
          echo "PBS file on Gadi: ${{ steps.recipe.outputs.gadi_path }}"
          echo "Check job submission output above for Job ID"
```

### PBS Generation Only (for external submission)
```yaml
name: Generate PBS Scripts
on: [push, pull_request]

jobs:
  generate-pbs:
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
      
      - name: Submit to HPC (using external ssh-action)
        uses: appleboy/ssh-action@v1
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
