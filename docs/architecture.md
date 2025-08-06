# Smart Recipe Runner

A unified GitHub Action for ESMValTool recipe management that intelligently handles configuration, deployment, and execution on HPC systems.

## Architecture Overview

The Smart Recipe Runner is designed with a modular architecture that separates concerns while providing a seamless user experience:

```
smart-recipe-runner/
├── action.yml                    # Main action definition
├── lib/
│   ├── config-manager.py         # Configuration management and analysis
│   ├── recipe-runner.py          # HPC execution logic
│   └── requirements.txt          # Python dependencies
├── docs/
│   ├── architecture.md           # This file
│   ├── configuration.md          # Configuration guide
│   └── troubleshooting.md        # Common issues and solutions
└── examples/
    ├── basic-usage.yml           # Simple workflow example
    ├── advanced-usage.yml        # Complex workflow example
    └── testing.yml               # Testing and validation
```

## Core Components

### 1. Action Definition (`action.yml`)

The main GitHub Action definition that:
- Defines all input parameters with sensible defaults
- Sets up the execution environment
- Orchestrates the configuration and execution flow
- Provides comprehensive outputs for workflow integration

Key features:
- **Input validation**: Ensures all required parameters are provided
- **Mode switching**: Supports different execution modes (run-only, setup-and-run, etc.)
- **Error handling**: Comprehensive error reporting and logging
- **Output generation**: Provides actionable outputs for downstream steps

### 2. Configuration Manager (`lib/config-manager.py`)

Intelligent configuration management system that:
- Analyzes recipe requirements automatically
- Generates optimized resource configurations
- Maintains configuration consistency across runs
- Provides fallback mechanisms for unknown recipes

#### Key Features:

**Heuristic Analysis**: Automatically determines resource requirements by analyzing:
- Recipe content and complexity
- Data source requirements
- Processing patterns
- Historical performance data

**Resource Classification**: Groups recipes into categories:
- `small`: Simple diagnostic recipes (2GB memory, 2 CPUs, 1 hour)
- `medium`: Standard analysis recipes (8GB memory, 4 CPUs, 3 hours)
- `large`: Complex climate analysis (16GB memory, 8 CPUs, 6 hours)
- `extra-large`: Heavy computational workloads (32GB memory, 16 CPUs, 12 hours)

**Self-Healing Configuration**: 
- Detects configuration drift
- Auto-regenerates configurations when needed
- Maintains backward compatibility
- Provides change detection and reporting

### 3. Recipe Runner (`lib/recipe-runner.py`)

HPC execution engine that:
- Handles SSH connections to compute systems
- Generates optimized PBS scripts
- Manages job submission and monitoring
- Provides comprehensive logging and error reporting

#### Execution Flow:

1. **Connection Setup**: Establishes secure SSH connection to HPC system
2. **Environment Preparation**: Sets up ESMValTool environment and dependencies
3. **Script Generation**: Creates optimized PBS job scripts based on resource requirements
4. **Job Submission**: Submits jobs to the queue system with proper resource allocation
5. **Monitoring**: Tracks job status and provides real-time feedback
6. **Result Collection**: Gathers outputs and artifacts for downstream processing

## Execution Modes

### 1. Run-Only Mode (`run-only`)
- Assumes configuration already exists
- Focuses purely on recipe execution
- Fastest execution for established workflows
- **Use case**: Production runs with stable configurations

### 2. Setup-and-Run Mode (`setup-and-run`)
- Comprehensive mode that handles everything
- Analyzes recipe and generates configuration
- Executes the recipe with optimized settings
- **Use case**: New recipes or when configuration needs updating

### 3. Config-Check Mode (`config-check`)
- Validates and analyzes existing configuration
- Generates new configuration if needed
- Provides detailed configuration reports
- **Use case**: Configuration validation and optimization

### 4. Dry-Run Mode (`dry-run`)
- Simulates execution without actual job submission
- Validates PBS script generation
- Checks resource allocation and parameters
- **Use case**: Testing and validation workflows

## Multiple Recipe Execution

### Matrix Strategy (Recommended)
The Smart Recipe Runner supports GitHub's matrix strategy for parallel execution of multiple recipes:

```yaml
# Setup job generates execution matrix
setup:
  outputs:
    matrix: ${{ steps.generate-matrix.outputs.matrix }}
  steps:
    - uses: ACCESS-NRI/smart-recipe-runner@v1
      with:
        recipe: all  # Triggers matrix generation
        generate_matrix: true
        recipe_filter: "recipe_.*"
        resource_filter: "all"

# Execute job runs recipes in parallel
execute:
  strategy:
    matrix: ${{ fromJson(needs.setup.outputs.matrix) }}
  steps:
    - uses: ACCESS-NRI/smart-recipe-runner@v1
      with:
        recipe: ${{ matrix.recipe }}
        mode: run-only
```

### Execution Strategies

1. **Matrix Execution** (Parallel)
   - Multiple recipes run simultaneously
   - Individual failure handling
   - Optimal resource utilization
   - **Best for**: Production workflows with many recipes

2. **Sequential Execution** (Serial)
   - Recipes run one after another
   - Lower resource requirements
   - Simplified error tracking
   - **Best for**: Resource-constrained environments

3. **Batch Execution** (All-in-one)
   - All recipes in single job
   - Simplest configuration
   - All-or-nothing execution
   - **Best for**: Simple test scenarios

### Recipe Filtering

The Smart Recipe Runner provides flexible recipe filtering:

**By Pattern**: Use regex to match recipe names
```yaml
recipe_filter: "recipe_(example|test).*"
```

**By Resource Group**: Filter by computational requirements
```yaml
resource_filter: "small"  # Only lightweight recipes
```

**Custom List**: Specify exact recipes
```yaml
recipe_filter: "recipe_example,recipe_validation,recipe_test"
```

**Discovery**: Automatically find all recipes
```yaml
recipe: all  # Discovers all available recipes
```

## Configuration Strategy

### Automatic Resource Detection

The configuration manager uses a multi-layered approach:

1. **Recipe Analysis**: Examines recipe YAML for complexity indicators
2. **Historical Data**: Leverages known recipe performance patterns
3. **Heuristic Classification**: Applies rules-based categorization
4. **Fallback Logic**: Provides safe defaults for unknown recipes

### Resource Allocation Logic

```python
def classify_recipe_complexity(recipe_content):
    # Multi-factor analysis
    factors = {
        'diagnostics': count_diagnostics(recipe_content),
        'variables': count_variables(recipe_content),
        'datasets': count_datasets(recipe_content),
        'time_range': analyze_time_range(recipe_content)
    }
    
    # Apply weighted scoring
    complexity_score = calculate_complexity_score(factors)
    
    # Map to resource groups
    return map_to_resource_group(complexity_score)
```

## Integration Patterns

### Workflow Integration

The Smart Recipe Runner integrates seamlessly with GitHub workflows for both single and multiple recipe execution:

**Single Recipe:**
```yaml
- name: Run Recipe Analysis
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: ${{ matrix.recipe }}
    mode: setup-and-run
    esmvaltool_version: main
  id: recipe-run

- name: Process Results
  if: steps.recipe-run.outputs.status == 'success'
  run: |
    echo "Job ID: ${{ steps.recipe-run.outputs.job_id }}"
    echo "Resource Group: ${{ steps.recipe-run.outputs.resource_group }}"
```

**Multiple Recipes (Matrix Strategy):**
```yaml
# Setup matrix
setup:
  steps:
    - uses: ACCESS-NRI/smart-recipe-runner@v1
      id: matrix
      with:
        recipe: all
        generate_matrix: true
        recipe_filter: "recipe_.*"

# Execute in parallel
execute:
  needs: setup
  strategy:
    matrix: ${{ fromJson(needs.setup.outputs.matrix) }}
  steps:
    - uses: ACCESS-NRI/smart-recipe-runner@v1
      with:
        recipe: ${{ matrix.recipe }}
        mode: run-only
```

**Batch Processing:**
```yaml
- name: Execute Multiple Recipes
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: all
    mode: setup-and-run
    recipe_filter: "climate_.*"
    resource_filter: "large"
```

### Error Handling Strategy

Comprehensive error handling at multiple levels:

1. **Input Validation**: Pre-execution parameter validation
2. **Configuration Errors**: Configuration generation and validation errors
3. **Connection Errors**: SSH and network connectivity issues
4. **Execution Errors**: HPC job submission and execution errors
5. **Resource Errors**: Resource allocation and queue system errors

## Performance Optimizations

### Resource Efficiency

- **Dynamic Allocation**: Resources allocated based on actual recipe requirements
- **Queue Optimization**: Smart queue selection based on resource needs
- **Parallel Processing**: Support for parallel execution patterns
- **Memory Management**: Optimized memory allocation to prevent OOM errors

### Execution Efficiency

- **Connection Reuse**: SSH connection pooling for multiple operations
- **Script Caching**: PBS script template caching and reuse
- **Configuration Caching**: Intelligent configuration caching and invalidation
- **Incremental Updates**: Only regenerate configuration when needed

## Extensibility

### Adding New Resource Groups

```python
RESOURCE_GROUPS = {
    'custom-group': {
        'memory': '64gb',
        'cpus': 32,
        'walltime': '24:00:00',
        'queue': 'hugemem'
    }
}
```

### Custom Classification Rules

```python
def custom_recipe_classifier(recipe_path, recipe_content):
    # Custom classification logic
    if 'machine_learning' in recipe_content:
        return 'ml-optimized'
    return None  # Fall back to default classification
```

## Security Considerations

### Credential Management

- **Secret Protection**: All credentials managed through GitHub secrets
- **Connection Security**: SSH key-based authentication only
- **Audit Logging**: Comprehensive logging of all access attempts
- **Principle of Least Privilege**: Minimal required permissions

### Data Protection

- **Secure Transfer**: All data transfers use encrypted channels
- **Temporary Files**: Automatic cleanup of temporary files and credentials
- **Access Control**: Restricted access to sensitive configuration files
- **Audit Trail**: Complete audit trail of all operations

## Monitoring and Observability

### Logging Strategy

- **Structured Logging**: JSON-formatted logs for machine processing
- **Multi-Level Logging**: Debug, info, warning, error levels
- **Contextual Information**: Rich context in all log messages
- **Performance Metrics**: Execution time and resource usage tracking

### Health Checks

- **Configuration Health**: Automatic validation of configuration integrity
- **System Health**: HPC system connectivity and resource availability checks
- **Dependency Health**: ESMValTool and environment dependency validation
- **Job Health**: Continuous monitoring of submitted jobs

This architecture provides a robust, scalable, and maintainable solution for ESMValTool recipe management while abstracting away the complexity from end users.
