# Smart Recipe Runner

[![Tests](https://github.com/rbeucher/smart-recipe-runner/workflows/Test%20Smart%20Recipe%20Runner/badge.svg)](https://github.com/rbeucher/smart-recipe-runner/actions/workflows/test.yml)

An intelligent GitHub Action for executing ESMValTool and COSIMA recipes with adaptive resource management on HPC systems.

## Installation

### Prerequisites
- Python 3.8 or higher  
- Git
- For job submission: SSH access to Gadi HPC system

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

### Matrix-based Recipe Execution

The action automatically detects execution mode based on inputs:
- **Matrix generation**: When `config_file` is provided
- **Recipe execution**: When used in GitHub Actions matrix strategy

#### Example: Configuration File Approach
```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.recipes.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
      - name: Generate Recipe Matrix  
        id: recipes
        uses: rbeucher/smart-recipe-runner@main
        with:
          config_file: 'examples/esmvaltool-all-recipes.yml'

  execute:
    needs: setup
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJson(needs.setup.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - name: Execute Recipe
        uses: rbeucher/smart-recipe-runner@main
        with:
          gadi_username: ${{ secrets.GADI_USERNAME }}
          gadi_ssh_key: ${{ secrets.GADI_SSH_KEY }}
          gadi_ssh_passphrase: ${{ secrets.GADI_SSH_PASSPHRASE }}
          submit_job: 'true'
```

### Recipe Repository Handling

The action automatically handles repository cloning and recipe discovery on Gadi:

**Repository Cloning Strategy:**
- **Login node cloning**: Repositories are cloned/updated on Gadi login nodes (which have internet access)
- **Compute node execution**: PBS jobs run on compute nodes using pre-cloned repositories (no internet needed)

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
| `config_file` | Path to YAML config file for multi-recipe execution | Yes* | - |
| `recipe_type` | Recipe type: `esmvaltool` or `cosima` | No | `esmvaltool` |
| `config` | Recipe configuration (JSON string, for matrix execution) | No | `{}` |
| `esmvaltool_version` | ESMValTool version (for esmvaltool recipes) | No | `main` |
| `conda_module` | Conda module to load | No | `conda/analysis3` |
| `project` | PBS project code (e.g., w40, kj13, etc.) | No | `w40` |
| `repository_url` | Repository URL for cloning | No | - |
| `gadi_username` | Gadi username for SSH connection | No | - |
| `gadi_ssh_key` | SSH private key for Gadi connection | No | - |
| `gadi_ssh_passphrase` | Passphrase for SSH private key (if password-protected) | No | - |
| `submit_job` | Whether to submit the job to Gadi (true/false) | No | `true` |
| `scripts_dir` | Directory on Gadi for scripts | No | `/scratch/$PROJECT/$USER/med-ci` |

**Notes:**
- `*` `config_file` is required for matrix generation mode
- For matrix execution, `recipe_name`, `recipe_type`, and `recipe_config` come from the matrix automatically

## Multi-Recipe Execution

The Smart Recipe Runner generates a matrix of recipes for parallel execution using GitHub Actions matrix strategy. There are two approaches:

### 1. Configuration File Approach

Create a YAML configuration file with multiple recipes:

```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.recipes.outputs.matrix }}
      recipe_count: ${{ steps.recipes.outputs.recipe_count }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate Recipe Matrix
        id: recipes
        uses: rbeucher/smart-recipe-runner@main
        with:
          config_file: 'path/to/multi-recipe-config.yml'
          selected_recipes: ${{ github.event.inputs.selected_recipes }}
          # ... other global parameters

  execute:
    needs: setup
    if: needs.setup.outputs.recipe_count > 0
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix: ${{ fromJson(needs.setup.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Execute Recipe
        uses: rbeucher/smart-recipe-runner@main
        with:
          # Recipe parameters come from matrix automatically
          # ... other common parameters
```

## Outputs

| Output | Description |
|--------|-------------|
| `matrix` | Recipe matrix for GitHub Actions (JSON) |
| `recipe_count` | Number of recipes found |


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
