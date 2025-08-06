# Configuration Guide

This guide explains how to configure and customize the Smart Recipe Runner for your ESMValTool workflows.

## Quick Start Configuration

The Smart Recipe Runner works out of the box with minimal configuration. For basic usage, you only need to provide GitHub secrets for HPC access:

```yaml
# Required secrets in your GitHub repository
GADI_USER: your-hpc-username
GADI_KEY: |
  <paste your SSH private key here>
  <multi-line SSH private key in OpenSSH format>
GADI_SCRIPTS_DIR: /path/to/your/scripts/directory
```

## Configuration Files

### Repository Configuration (`repository-config.yml`)

The Smart Recipe Runner automatically generates and maintains a configuration file at `.github/config/repository-config.yml`. This file contains:

```yaml
# Auto-generated configuration
version: "1.0"
generated_at: "2024-01-15T10:30:00Z"
generator: "smart-recipe-runner"

# Recipe-specific configurations
recipes:
  - name: "recipe_example"
    group: "small"
    memory: "2gb"
    cpus: 2
    walltime: "01:00:00"
    queue: "normal"
    
  - name: "recipe_climate_analysis"
    group: "large"
    memory: "16gb"
    cpus: 8
    walltime: "06:00:00"
    queue: "normal"

# Resource group definitions
resource_groups:
  small:
    memory: "2gb"
    cpus: 2
    walltime: "01:00:00"
    queue: "normal"
    description: "Light diagnostic recipes"
  
  medium:
    memory: "8gb"
    cpus: 4
    walltime: "03:00:00"
    queue: "normal"
    description: "Standard analysis recipes"
    
  large:
    memory: "16gb"
    cpus: 8
    walltime: "06:00:00"
    queue: "normal"
    description: "Complex climate analysis"
    
  extra-large:
    memory: "32gb"
    cpus: 16
    walltime: "12:00:00"
    queue: "normal"
    description: "Heavy computational workloads"
```

### User Configuration (`config-user.yml`)

Your ESMValTool user configuration should be placed in the `config/` directory:

```yaml
# ESMValTool user configuration
output_dir: /path/to/output
auxiliary_data_dir: /path/to/auxiliary_data
rootpath:
  CMIP6: /path/to/cmip6/data
  OBS: /path/to/obs/data
drs:
  CMIP6: ESGF
  OBS: default
log_level: info
exit_on_warning: false
output_file_type: png
compress_netcdf: false
save_intermediary_cubes: false
remove_preproc_dir: true
max_parallel_tasks: null
```

## Action Configuration

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
    # Recipe configuration
    recipe: recipe_climate_analysis
    mode: setup-and-run
    
    # ESMValTool configuration
    esmvaltool_version: main
    config_file: config/config-user-custom.yml
    
    # Resource overrides (optional)
    memory: 32gb
    cpus: 16
    walltime: "08:00:00"
    queue: hugemem
    
    # Execution options
    force_config_regeneration: true
    debug_mode: true
```

## Input Parameters Reference

### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `recipe` | Name of the ESMValTool recipe to run | `recipe_example` |

### Optional Parameters

#### Recipe Configuration
| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `mode` | Execution mode | `setup-and-run` | `run-only`, `config-check`, `dry-run` |
| `esmvaltool_version` | ESMValTool version/branch | `main` | `v2.8.0`, `develop` |
| `config_file` | User configuration file path | `config/config-user.yml` | `config/custom.yml` |

#### Resource Configuration
| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `memory` | Memory allocation | Auto-detected | `2gb`, `16gb`, `32gb` |
| `cpus` | CPU count | Auto-detected | `2`, `8`, `16` |
| `walltime` | Maximum runtime | Auto-detected | `01:00:00`, `12:00:00` |
| `queue` | PBS queue name | `normal` | `express`, `hugemem` |

#### Execution Options
| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `force_config_regeneration` | Force config regeneration | `false` | `true`, `false` |
| `debug_mode` | Enable debug logging | `false` | `true`, `false` |

## Resource Groups Explained

### Small (`small`)
- **Memory**: 2GB
- **CPUs**: 2
- **Walltime**: 1 hour
- **Use cases**: Simple diagnostics, data validation, quick analyses
- **Example recipes**: `recipe_check_obs`, basic plotting recipes

### Medium (`medium`)
- **Memory**: 8GB
- **CPUs**: 4
- **Walltime**: 3 hours
- **Use cases**: Standard analysis workflows, multi-variable diagnostics
- **Example recipes**: Most CMIP evaluation recipes

### Large (`large`)
- **Memory**: 16GB
- **CPUs**: 8
- **Walltime**: 6 hours
- **Use cases**: Complex climate analysis, multi-model ensembles
- **Example recipes**: Climate change projection recipes, comprehensive evaluations

### Extra-Large (`extra-large`)
- **Memory**: 32GB
- **CPUs**: 16
- **Walltime**: 12 hours
- **Use cases**: Intensive computational work, large datasets, machine learning
- **Example recipes**: High-resolution analysis, statistical downscaling

## Automatic Classification

The Smart Recipe Runner uses heuristic analysis to automatically classify recipes:

### Classification Factors

1. **Diagnostic Count**: Number of diagnostic scripts in the recipe
2. **Variable Count**: Number of variables being processed
3. **Dataset Count**: Number of datasets being analyzed
4. **Time Range**: Temporal scope of the analysis
5. **Spatial Resolution**: Resolution of the data being processed

### Override Classification

You can override automatic classification by:

1. **Adding recipe to known recipes**: Modify the configuration file
2. **Using resource parameters**: Override specific resources in the action call
3. **Creating custom resource groups**: Define new resource categories

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

## Environment Variables

### Required Environment Variables

Set these in your GitHub repository secrets:

```bash
GADI_USER         # Your HPC username
GADI_KEY          # Your SSH private key
GADI_SCRIPTS_DIR  # Directory for script storage on HPC
GITHUB_TOKEN      # GitHub access token (usually automatic)
```

### Optional Environment Variables

```bash
# ESMValTool configuration
ESMVALTOOL_VERSION    # Override default version
CONFIG_FILE           # Override default config file

# Resource configuration
DEFAULT_MEMORY        # Default memory allocation
DEFAULT_CPUS          # Default CPU count
DEFAULT_WALLTIME      # Default walltime
DEFAULT_QUEUE         # Default queue

# Debugging
DEBUG_MODE            # Enable debug logging
VERBOSE_OUTPUT        # Enable verbose output
```

## Custom Resource Groups

You can define custom resource groups for specialized workloads:

```yaml
# In repository-config.yml
resource_groups:
  ml-optimized:
    memory: "64gb"
    cpus: 32
    walltime: "24:00:00"
    queue: "hugemem"
    description: "Machine learning workloads"
    
  data-intensive:
    memory: "8gb"
    cpus: 4
    walltime: "12:00:00"
    queue: "normal"
    description: "I/O intensive operations"
```

## Troubleshooting Configuration

### Common Issues

1. **Recipe not found**: Ensure recipe file exists in recipes directory
2. **SSH connection failed**: Check GADI_USER and GADI_KEY secrets
3. **Resource allocation failed**: Verify queue limits and resource requests
4. **Configuration not updating**: Set `force_config_regeneration: true`

### Debug Mode

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
