# Smart Recipe Runner Architecture

A streamlined GitHub Action for ESMValTool and COSIMA recipe execution that generates optimized PBS scripts for HPC systems.

## Architecture Overview

The Smart Recipe Runner follows a simple, focused architecture with two core components:

```
smart-recipe-runner/
├── action.yml                    # Main action definition
├── lib/
│   ├── config-manager.py         # Configuration analysis and management
│   ├── recipe-runner.py          # PBS script generation
│   └── requirements.txt          # Python dependencies
├── docs/
│   ├── architecture.md           # This file
│   ├── configuration.md          # Configuration guide
│   └── troubleshooting.md        # Troubleshooting guide
└── examples/
    ├── basic-usage.yml           # Simple workflow example
    ├── advanced-usage.yml        # Complex workflow example
    ├── cosima-usage.yml          # COSIMA workflow example
    └── matrix-testing.yml        # Matrix testing example
```

## Core Components

### 1. Action Definition (`action.yml`)

The main GitHub Action definition that:
- Defines input parameters with sensible defaults
- Sets up the execution environment
- Orchestrates the PBS script generation flow
- Provides structured outputs for workflow integration

Key features:
- **Input validation**: Ensures required parameters are provided
- **Recipe type switching**: Supports ESMValTool and COSIMA recipes
- **Error handling**: Comprehensive error reporting and logging
- **Clean outputs**: Provides PBS filename for ssh-action integration

### 2. Configuration Manager (`lib/config-manager.py`)

Intelligent configuration analysis system that:
- Analyzes recipe requirements automatically
- Generates optimized resource configurations
- Maintains configuration consistency across runs
- Provides fallback mechanisms for unknown recipes

#### Key Features:

**Recipe Complexity Analysis**: Automatically determines resource requirements by analyzing:
- Recipe file content and structure
- Dataset requirements and complexity
- Diagnostic patterns and computational load
- Known resource patterns from community recipes

**Resource Classification**: Groups recipes into categories:
- `light`: Simple diagnostic recipes (copyq, 16GB memory, 1 hour)
- `medium`: Standard analysis recipes (normal queue, 32GB memory, 2 hours)
- `heavy`: Complex climate analysis (normal queue, 64GB memory, 4 hours)
- `megamem`: Memory-intensive workloads (megamem queue, 256GB memory, 8 hours)

**Smart Configuration Management**: 
- Detects when configuration needs updating
- Auto-regenerates configurations when recipe changes are detected
- Maintains configuration consistency across runs
- Provides fallback configurations for unknown recipes

### 3. Recipe Runner (`lib/recipe-runner.py`)

PBS script generation engine that:
- Creates HPC-optimized job scripts for different recipe types
- Handles environment setup and dependency management
- Supports both ESMValTool and COSIMA workflows
- Provides structured outputs for ssh-action integration

#### Key Features:

**Multi-Platform Support**:
- **ESMValTool recipes**: Complete environment setup with conda and ESMValTool installation
- **COSIMA recipes**: Ocean analysis workflows with Jupyter notebook execution
- **Custom repositories**: Support for user-defined recipe repositories

**PBS Script Optimization**:
- Resource allocation based on recipe complexity analysis
- Environment setup with proper conda module loading
- Repository cloning and dependency management
- Structured logging and output management

**Clean Integration**:
- Generates PBS scripts as files for ssh-action to upload and submit
- No complex SSH handling within the action itself
- Simple status reporting for workflow integration

## Execution Flow

The simplified execution flow consists of three main phases:

### 1. Configuration Analysis
- Load or generate configuration based on recipe analysis
- Determine optimal resource allocation for the recipe
- Apply any user-provided configuration overrides

### 2. PBS Script Generation
- Create optimized PBS script based on recipe type (ESMValTool/COSIMA)
- Include proper resource allocation and environment setup
- Handle repository cloning and dependency installation
- Structure script for reliable execution on HPC systems

### 3. Output Delivery
- Save PBS script to file system
- Provide script filename as output for ssh-action integration
- Report generation status and any configuration updates

## Recipe Type Support

### ESMValTool Recipes
- **Environment**: Automated conda environment setup with specified ESMValTool version
- **Repository**: Clones ESMValTool repository (main, latest, or specific versions)
- **Configuration**: Uses provided config JSON or falls back to system defaults
- **Execution**: Runs `esmvaltool run` with appropriate resource allocation

### COSIMA Recipes  
- **Environment**: Ocean analysis environment with Jupyter and scientific Python stack
- **Repository**: Clones COSIMA recipes or user-specified repository
- **Configuration**: Optimized for ocean modeling workflows
- **Execution**: Notebook-based execution with COSIMA-specific resource allocation

## Matrix Testing Support

The configuration manager includes built-in support for matrix testing:

```yaml
# Generate execution matrix for multiple recipes
- name: Generate Matrix
  id: matrix
  uses: rbeucher/smart-recipe-runner@main
  with:
    recipe_name: 'all'  # Triggers matrix generation
    recipe_filter: 'recipe_.*'
    resource_filter: 'all'
    max_parallel: 8

# Execute recipes in parallel using matrix
- name: Execute Recipes
  strategy:
    matrix: ${{ fromJson(steps.matrix.outputs.matrix) }}
  uses: rbeucher/smart-recipe-runner@main
  with:
    recipe_type: 'esmvaltool'
    recipe_name: ${{ matrix.recipe }}
```

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
## Integration with ssh-action

The Smart Recipe Runner is designed to work seamlessly with ssh-action for HPC job submission:

### Workflow Integration Pattern

```yaml
jobs:
  generate-pbs:
    runs-on: ubuntu-latest
    outputs:
      pbs_filename: ${{ steps.generate.outputs.pbs_filename }}
    steps:
      - uses: actions/checkout@v4
      - name: Generate PBS Script
        id: generate
        uses: rbeucher/smart-recipe-runner@main
        with:
          recipe_type: 'esmvaltool'
          recipe_name: 'recipe_python.yml'
          
  submit-job:
    needs: generate-pbs
    runs-on: ubuntu-latest
    steps:
      - name: Submit to HPC
        uses: ACCESS-NRI/ssh-action@v1
        with:
          host: 'gadi.nci.org.au'
          username: ${{ secrets.GADI_USERNAME }}
          key: ${{ secrets.GADI_SSH_KEY }}
          script: |
            cd /scratch/$USER/scripts
            qsub ${{ needs.generate-pbs.outputs.pbs_filename }}
```

### Resource Classification Logic

The configuration manager uses a multi-factor analysis to classify recipes:

```python
def analyze_recipe_complexity(recipe_path):
    # Analyze recipe structure
    complexity_score = 0
    
    # Check datasets (more datasets = more complexity)
    if len(datasets) > 10: complexity_score += 2
    elif len(datasets) > 5: complexity_score += 1
        
    # Check diagnostics (more diagnostics = more processing)
    if len(diagnostics) > 3: complexity_score += 2
    elif len(diagnostics) > 1: complexity_score += 1
        
    # Check for memory-intensive keywords
    memory_keywords = ['climwip', 'ipcc', 'cmip6', 'bias', 'multimodel']
    for keyword in memory_keywords:
        if keyword in content_lower: complexity_score += 1
            
    # Map score to resource group
    if complexity_score >= 4: return 'heavy'
    elif complexity_score >= 2: return 'medium'
    else: return 'light'
```

### PBS Script Templates

**ESMValTool Template:**
```bash
#!/bin/bash
#PBS -N {recipe_name}
#PBS -l mem={memory}
#PBS -l ncpus={ncpus}
#PBS -l walltime={walltime}
#PBS -q {queue}
#PBS -P {project}

module load {conda_module}
cd $SCRIPTS_DIR

# Clone ESMValTool repository
git clone {repository_url} ESMValTool-ci
cd ESMValTool-ci
pip install -e .

# Execute recipe
esmvaltool run {recipe_name} --config_file={config_file}
```

**COSIMA Template:**
```bash
#!/bin/bash
#PBS -N cosima_{notebook_name}
#PBS -l mem={memory}
#PBS -l ncpus={ncpus}
#PBS -l walltime={walltime}
#PBS -q {queue}
#PBS -P {project}

module load {conda_module}
cd $SCRIPTS_DIR

# Clone COSIMA recipes
git clone {repository_url} cosima-recipes
cd cosima-recipes

# Execute notebook
jupyter nbconvert --to notebook --execute {notebook_name}.ipynb
```

## Extension Points

### Adding New Recipe Types

To add support for a new recipe type:

1. **Add recipe type logic** in `recipe-runner.py`:
```python
def generate_pbs_script(self, recipe_name, config, recipe_type):
    if recipe_type.lower() == 'new-type':
        return self.generate_newtype_pbs_script(recipe_name, config)
    # ... existing logic
```

2. **Create type-specific PBS generator**:
```python
def generate_newtype_pbs_script(self, recipe_name, config):
    # Custom PBS script generation for new recipe type
    return pbs_script_content
```

3. **Update action.yml** to include new recipe type in documentation

### Custom Resource Classifications

Users can extend resource classifications by:

1. Modifying the `known_heavy_recipes` and `known_megamem_recipes` sets
2. Adding custom analysis logic in `analyze_recipe_complexity()`
3. Defining new resource groups in the `default_resources` configuration

## Performance Considerations

### Configuration Caching
- Configuration hash-based change detection prevents unnecessary regeneration
- File-based caching of recipe analysis results
- Intelligent fallback to previous configurations when analysis fails

### PBS Script Optimization
- Template-based script generation for consistent formatting
- Minimal resource allocation to reduce queue wait times
- Optimized environment setup to reduce job startup time

### Error Recovery
- Graceful fallback to default configurations when analysis fails
- Comprehensive error reporting for debugging
- Safe defaults that work for most recipes

This simplified architecture focuses on the core functionality while maintaining flexibility for future extensions.
