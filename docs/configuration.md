# Configuration Guide

This guide explains how to configure and use the Smart Recipe Runner for ESMValTool and COSIMA workflows.

## Quick Start Configuration

The Smart Recipe Runner works with minimal configuration. For basic usage, you only need to specify the recipe type and recipe name:

```yaml
- name: Test ESMValTool Recipe
  uses: rbeucher/smart-recipe-runner@main
  with:
    recipe_type: 'esmvaltool'
    recipe_name: 'recipe_python.yml'
```

## Input Parameters

### Required Parameters

| Parameter | Description | Values |
|-----------|-------------|--------|
| `recipe_type` | Type of recipe to execute | `esmvaltool`, `cosima` |
| `recipe_name` | Name of the recipe file | Recipe filename (e.g., `recipe_python.yml`) |

### Optional Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `config` | Configuration JSON string | `{}` | `'{"rootpath": {"default": "/data"}}'` |
| `esmvaltool_version` | ESMValTool version (for esmvaltool recipes) | `main` | `main`, `latest`, `v2.13.0` |
| `conda_module` | Conda module to load | `conda/access-med` | `conda/access-med` |
| `repository_url` | Custom repository URL | - | `https://github.com/myorg/recipes` |

## Configuration Examples

### Basic ESMValTool Recipe
```yaml
- name: Test Python Recipe
  uses: rbeucher/smart-recipe-runner@main
  with:
    recipe_type: 'esmvaltool'
    recipe_name: 'recipe_python.yml'
    esmvaltool_version: 'main'
```

### ESMValTool with Custom Configuration
```yaml
- name: Test Recipe with Config
  uses: rbeucher/smart-recipe-runner@main
  with:
    recipe_type: 'esmvaltool'
    recipe_name: 'recipe_ocean.yml'
    config: |
      {
        "rootpath": {
          "CMIP6": "/g/data/ks32/CMIP6",
          "OBS": "/g/data/ks32/obs"
        },
        "output_dir": "/scratch/abc123/esmvaltool_output"
      }
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

### Custom Repository
```yaml
- name: Test Custom Repository
  uses: rbeucher/smart-recipe-runner@main
  with:
    recipe_type: 'esmvaltool'
    recipe_name: 'my_custom_recipe.yml'
    repository_url: 'https://github.com/myorg/my-esmvaltool-recipes'
    esmvaltool_version: 'v2.12.0'
```

### Basic Configuration

```yaml
- name: Run Recipe
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: recipe_example
    # All other parameters use intelligent defaults
```

### Advanced Configuration

```yaml
- name: Run Complex Recipe
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
## Matrix Testing

The Smart Recipe Runner supports matrix testing for executing multiple recipes:

### Basic Matrix Testing
```yaml
strategy:
  matrix:
    recipe_type: ['esmvaltool']
    recipe_name: 
      - 'recipe_python.yml'
      - 'recipe_ocean_example.yml'
      - 'recipe_climate.yml'
      
steps:
  - name: Test Recipe Matrix
    uses: rbeucher/smart-recipe-runner@main
    with:
      recipe_type: ${{ matrix.recipe_type }}
      recipe_name: ${{ matrix.recipe_name }}
```

### Advanced Matrix with Different Configurations
```yaml
strategy:
  matrix:
    include:
      - recipe_type: 'esmvaltool'
        recipe_name: 'recipe_python.yml'
        esmvaltool_version: 'main'
      - recipe_type: 'esmvaltool'
        recipe_name: 'recipe_ocean.yml'
        esmvaltool_version: 'v2.12.0'
      - recipe_type: 'cosima'
        recipe_name: 'ocean_analysis'
        repository_url: 'https://github.com/COSIMA/cosima-recipes'
      
steps:
  - name: Test Recipe
    uses: rbeucher/smart-recipe-runner@main
    with:
      recipe_type: ${{ matrix.recipe_type }}
      recipe_name: ${{ matrix.recipe_name }}
      esmvaltool_version: ${{ matrix.esmvaltool_version }}
      repository_url: ${{ matrix.repository_url }}
```

## Resource Allocation

The Smart Recipe Runner automatically allocates resources based on recipe analysis:

### Resource Categories

| Category | Queue | Memory | NCPUs | Walltime | Use Case |
|----------|-------|---------|-------|----------|----------|
| `light` | copyq | 16GB | 2 | 1:00:00 | Simple diagnostics, quick plots |
| `medium` | normal | 32GB | 4 | 2:00:00 | Standard analysis workflows |
| `heavy` | normal | 64GB | 8 | 4:00:00 | Complex climate analysis |
| `megamem` | megamem | 256GB | 16 | 8:00:00 | Memory-intensive workloads |

### Automatic Classification

The system analyzes recipes using multiple factors:

```yaml
# Complexity factors analyzed:
- Number of datasets (more datasets = higher complexity)
- Number of diagnostics (more diagnostics = more processing)
- Memory-intensive keywords (climwip, ipcc, cmip6, bias, multimodel)
- Time-intensive operations (timeseries, trend, climatology)
```

### Known Recipe Classifications

Some recipes are pre-classified based on community knowledge:

**Heavy Recipes:**
- `recipe_anav13jclim`
- `recipe_bock20jgr_fig_6-7`
- `recipe_check_obs`
- `recipe_collins13ipcc`

**Megamem Recipes:**
- `recipe_collins13ipcc`
- `recipe_schlund20esd`  
- `recipe_ipccwg1ar6ch3_fig_3_42_a`

## Integration with ssh-action

The Smart Recipe Runner generates PBS scripts that can be submitted via ssh-action:

### Complete Workflow Example
```yaml
name: ESMValTool Recipe Testing

on: [push, pull_request]

jobs:
  generate-pbs:
    runs-on: ubuntu-latest
    outputs:
      pbs_filename: ${{ steps.generate.outputs.pbs_filename }}
      status: ${{ steps.generate.outputs.status }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate PBS Script
        id: generate
        uses: rbeucher/smart-recipe-runner@main
        with:
          recipe_type: 'esmvaltool'
          recipe_name: 'recipe_python.yml'
          config: |
            {
              "rootpath": {
                "CMIP6": "/g/data/ks32/CMIP6"
              }
            }
  
  submit-to-hpc:
    needs: generate-pbs
    if: needs.generate-pbs.outputs.status == 'pbs-generated'
    runs-on: ubuntu-latest
    steps:
      - name: Submit Job to Gadi
        uses: ACCESS-NRI/ssh-action@v1
        with:
          host: 'gadi.nci.org.au'
          username: ${{ secrets.GADI_USERNAME }}
          key: ${{ secrets.GADI_SSH_KEY }}
          script: |
            cd /scratch/$USER/scripts
            qsub ${{ needs.generate-pbs.outputs.pbs_filename }}
```

## Troubleshooting

### Common Issues

**Recipe not found:**
- Ensure the recipe name matches exactly (case-sensitive)
- Check that the recipe exists in the specified repository
- Verify repository URL is accessible

**Resource allocation issues:**
- Check that the PBS queue is available on your HPC system
- Verify project allocation has sufficient resources
- Consider overriding resource classification for problematic recipes

**Configuration errors:**
- Validate JSON syntax in config parameter
- Ensure all required paths exist on the HPC system
- Check ESMValTool version compatibility

### Debug Mode

Enable verbose logging by setting environment variables:
```yaml
env:
  DEBUG: true
  VERBOSE: true
```

```yaml
# Override example
- name: Run with Custom Resources
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: recipe_custom
    memory: 64gb
    cpus: 24
    walltime: "24:00:00"
    queue: hugemem
```

## Queue Configuration

### Available Queues (Gadi)

| Queue | Description | Max CPUs | Max Memory | Max Walltime |
|-------|-------------|----------|------------|--------------|
| `normal` | Standard queue | 48 | 192GB | 48 hours |
| `express` | High priority, fast turnaround | 48 | 192GB | 12 hours |
| `copyq` | Data movement operations | 1 | 4GB | 10 hours |
| `hugemem` | Large memory jobs | 48 | 1470GB | 48 hours |

### Queue Selection Logic

The Smart Recipe Runner automatically selects appropriate queues based on resource requirements:

```python
def select_queue(memory, cpus, walltime):
    if memory > "192gb":
        return "hugemem"
    elif walltime < "01:00:00" and cpus <= 12:
        return "express"
    else:
        return "normal"
```

## Output Files

The Smart Recipe Runner generates the following outputs:

### PBS Script
- **Filename**: `launch_{recipe_name}.pbs`
- **Content**: Optimized PBS script for HPC execution
- **Location**: Current working directory
- **Purpose**: Ready for upload and submission via ssh-action

### Configuration Cache
- **Purpose**: Speeds up subsequent runs by caching recipe analysis
- **Location**: Automatically managed
- **Invalidation**: Automatic when recipes change

## Best Practices

### Recipe Selection
- Use descriptive recipe names that match your analysis purpose
- Keep recipes focused on specific tasks for better resource allocation
- Test complex recipes with simpler versions first

### Configuration Management
- Use JSON format for configuration parameters
- Keep paths relative to HPC system structure
- Test configurations with small datasets first

### Resource Optimization
- Let automatic classification handle resource allocation when possible
- Override only when you know specific requirements
- Monitor actual resource usage to optimize future runs

### Workflow Integration
- Separate PBS generation from job submission for better error handling
- Use matrix strategies for testing multiple recipes efficiently
- Implement proper error handling and cleanup

This simplified configuration system focuses on the core functionality while providing flexibility for advanced use cases.

Enable debug mode for detailed logging:

```yaml
- name: Debug Recipe Run
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: problematic_recipe
    debug_mode: true
    mode: dry-run  # Test without actual execution
```

### Validation

Use config-check mode to validate your configuration:

```yaml
- name: Validate Configuration
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: recipe_to_test
    mode: config-check
    force_config_regeneration: true
```

## Best Practices

### 1. Start Small
Begin with simple recipes and default configurations before customizing.

### 2. Use Dry-Run Mode
Test new configurations with `mode: dry-run` before actual execution.

### 3. Monitor Resource Usage
Review job outputs to optimize resource allocation over time.

### 4. Version Control Configuration
Keep configuration files in version control for reproducibility.

### 5. Document Custom Groups
Document any custom resource groups for team collaboration.

### 6. Regular Updates
Periodically regenerate configuration to incorporate new recipes and optimizations.

## Migration from Legacy Actions

If migrating from the old deploy/run action combination:

```yaml
# OLD approach
- uses: ACCESS-NRI/deploy-recipe-cicd@main
- uses: ACCESS-NRI/run-recipe@main

# NEW approach
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: ${{ matrix.recipe }}
    mode: setup-and-run
```

The Smart Recipe Runner automatically handles all configuration and execution tasks that previously required two separate actions.
