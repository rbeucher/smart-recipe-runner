#!/usr/bin/env python3
"""
Smart Recipe Runner for ESMValTool CI/CD

This module handles the execution of ESMValTool recipes on HPC systems,
including PBS job generation, submission, and monitoring.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict


class SmartRecipeRunner:
    """HPC PBS script generator for ESMValTool and COSIMA recipes."""
    
    def __init__(self, log_dir: str = './logs'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        print("🎯 SmartRecipeRunner: Configured for HPC PBS script generation")

    def generate_esmvaltool_pbs_script(self, recipe_name: str, config: Dict, 
                                      esmvaltool_version: str, conda_module: str, project: str = 'w40') -> str:
        """Generate PBS script for ESMValTool recipe execution on Gadi."""
        
        # Determine config file path based on version
        config_file_version = esmvaltool_version if esmvaltool_version != 'main' else 'main'
        config_file = f"/g/data/kj13/admin/ESMValTool/.esmvaltool/config-user-{config_file_version}.yml"
        fallback_config = "/g/data/kj13/admin/ESMValTool/.esmvaltool/config-user.yml"
        
        # Build max_parallel_tasks parameter if specified
        max_parallel_tasks = config.get('max_parallel_tasks')
        parallel_tasks_param = f" --max_parallel_tasks={max_parallel_tasks}" if max_parallel_tasks else ""
        
        # Use storage from config or default
        pbs_storage = config.get('storage', "gdata/kj13+gdata/fs38+gdata/oi10+gdata/rr3+gdata/xp65+gdata/al33+gdata/rt52+gdata/zz93+gdata/cb20")
        
        pbs_script = f"""#!/bin/bash -l 
#PBS -S /bin/bash
#PBS -P {project}
#PBS -l storage={pbs_storage}
#PBS -N {recipe_name}-{esmvaltool_version}
#PBS -W block=true
#PBS -W umask=037
#PBS -l wd
#PBS -o /g/data/kj13/admin/ESMValTool/logs/{recipe_name}-{esmvaltool_version}.out
#PBS -e /g/data/kj13/admin/ESMValTool/logs/{recipe_name}-{esmvaltool_version}.err
#PBS -q {config['queue']}
#PBS -l walltime={config['walltime']}
#PBS -l mem={config['memory']}

module purge 
module load pbs 

# Load version-specific conda environment
module use /g/data/xp65/public/modules
module load {conda_module}

# Set version-specific config
export ESMVAL_USER_CONFIG={config_file}

# Fall back to main config if version-specific doesn't exist
if [ ! -f "$ESMVAL_USER_CONFIG" ]; then
  export ESMVAL_USER_CONFIG={fallback_config}
fi

echo "=== ESMValTool Recipe Execution ==="
echo "Recipe: {recipe_name}"
echo "Version: {esmvaltool_version}"
echo "Resource group: {config['group']}"
echo "Job started at: $(date)"
echo "Config file: $ESMVAL_USER_CONFIG"

# Set base directories - repository should already be cloned by the action
SCRIPTS_DIR="${{PBS_O_WORKDIR:-/scratch/${{USER}}/esmvaltool-ci}}"
ESMVAL_PATH="$SCRIPTS_DIR/../ESMValTool-ci"
RECIPES_PATH="esmvaltool/recipes"

echo "📁 Using pre-cloned ESMValTool repository..."
echo "Scripts directory: $SCRIPTS_DIR"
echo "ESMValTool path: $ESMVAL_PATH"
echo "Recipes path: $ESMVAL_PATH/$RECIPES_PATH"

# Verify repository exists (should have been cloned by the action)
if [ ! -d "$ESMVAL_PATH" ]; then
    echo "❌ ERROR: ESMValTool repository not found at $ESMVAL_PATH"
    echo "The repository should have been cloned before job submission."
    echo "Please check the action configuration and ensure repository cloning succeeded."
    exit 1
fi

# Check if recipe exists - search in multiple locations
echo "🔍 Searching for recipe: {recipe_name}"

# Define possible recipe locations
recipe_locations=(
    "$ESMVAL_PATH/$RECIPES_PATH/{recipe_name}"
    "$ESMVAL_PATH/$RECIPES_PATH/{recipe_name}.yml"
    "$ESMVAL_PATH/$RECIPES_PATH/examples/{recipe_name}"
    "$ESMVAL_PATH/$RECIPES_PATH/examples/{recipe_name}.yml"
    "$ESMVAL_PATH/$RECIPES_PATH/*/recipe_{recipe_name}.yml"
)

recipe_file=""
for location in "${{recipe_locations[@]}}"; do
    if [ -f "$location" ]; then
        recipe_file="$location"
        echo "✅ Found recipe at: $recipe_file"
        break
    fi
done

if [ -z "$recipe_file" ]; then
    echo "❌ ERROR: Recipe '{recipe_name}' not found in ESMValTool repository"
    echo "Searched in the following locations:"
    for location in "${{recipe_locations[@]}}"; do
        echo "  - $location"
    done
    echo ""
    echo "Available recipes in main directory:"
    ls -la "$ESMVAL_PATH/$RECIPES_PATH/"*.yml 2>/dev/null || echo "  No .yml files found"
    echo ""
    echo "Available recipes in examples directory:"
    ls -la "$ESMVAL_PATH/$RECIPES_PATH/examples/"*.yml 2>/dev/null || echo "  No .yml files found"
    exit 1
fi

echo "🚀 Running recipe: $recipe_file"

# Run ESMValTool with version-specific configuration
esmvaltool run --config_file "$ESMVAL_USER_CONFIG" "$recipe_file"{parallel_tasks_param}

echo "Job completed at: $(date)"
"""
        return pbs_script

    def generate_cosima_pbs_script(self, recipe_name: str, config: Dict, project: str = 'w40') -> str:
        """Generate PBS script for COSIMA recipe execution on Gadi."""
        
        # Use storage from config or default
        pbs_storage = config.get('storage', "gdata/kj13+gdata/fs38+gdata/oi10+gdata/rr3+gdata/v45+gdata/hh5")
        
        pbs_script = f"""#!/bin/bash -l 
#PBS -S /bin/bash
#PBS -P {project}
#PBS -l storage={pbs_storage}
#PBS -N {recipe_name}-cosima
#PBS -W block=true
#PBS -W umask=037
#PBS -l wd
#PBS -o /g/data/kj13/admin/COSIMA/logs/{recipe_name}.out
#PBS -e /g/data/kj13/admin/COSIMA/logs/{recipe_name}.err
#PBS -q {config['queue']}
#PBS -l walltime={config['walltime']}
#PBS -l mem={config['memory']}

module purge 
module load pbs 

# Load COSIMA environment
module use /g/data/hh5/public/modules
module load conda/analysis3

echo "=== COSIMA Recipe Execution ==="
echo "Recipe: {recipe_name}"
echo "Resource group: {config['group']}"
echo "Job started at: $(date)"

# Set base directories - repository should already be cloned by the action
SCRIPTS_DIR="${{PBS_O_WORKDIR:-/scratch/${{USER}}/cosima-ci}}"
COSIMA_PATH="$SCRIPTS_DIR/../COSIMA-recipes-ci"

echo "📁 Using pre-cloned COSIMA repository..."
echo "Scripts directory: $SCRIPTS_DIR"
echo "COSIMA path: $COSIMA_PATH"

# Verify repository exists (should have been cloned by the action)
if [ ! -d "$COSIMA_PATH" ]; then
    echo "❌ ERROR: COSIMA repository not found at $COSIMA_PATH"
    echo "The repository should have been cloned before job submission."
    echo "Please check the action configuration and ensure repository cloning succeeded."
    exit 1
fi

# Check if recipe exists - search in multiple locations
echo "🔍 Searching for COSIMA recipe: {recipe_name}"

# Define possible recipe locations
recipe_locations=(
    "$COSIMA_PATH/{recipe_name}"
    "$COSIMA_PATH/{recipe_name}.py"
    "$COSIMA_PATH/{recipe_name}.ipynb"
    "$COSIMA_PATH/notebooks/{recipe_name}"
    "$COSIMA_PATH/notebooks/{recipe_name}.py"
    "$COSIMA_PATH/notebooks/{recipe_name}.ipynb"
    "$COSIMA_PATH/scripts/{recipe_name}"
    "$COSIMA_PATH/scripts/{recipe_name}.py"
    "$COSIMA_PATH/examples/{recipe_name}"
    "$COSIMA_PATH/examples/{recipe_name}.py"
    "$COSIMA_PATH/examples/{recipe_name}.ipynb"
)

recipe_file=""
for location in "${{recipe_locations[@]}}"; do
    if [ -f "$location" ]; then
        recipe_file="$location"
        echo "✅ Found recipe at: $recipe_file"
        break
    fi
done

if [ -z "$recipe_file" ]; then
    echo "❌ ERROR: Recipe '{recipe_name}' not found in COSIMA repository"
    echo "Searched in the following locations:"
    for location in "${{recipe_locations[@]}}"; do
        echo "  - $location"
    done
    echo ""
    echo "Available Python scripts:"
    find "$COSIMA_PATH" -name "*.py" -type f 2>/dev/null | head -10 || echo "  No .py files found"
    echo ""
    echo "Available Jupyter notebooks:"
    find "$COSIMA_PATH" -name "*.ipynb" -type f 2>/dev/null | head -10 || echo "  No .ipynb files found"
    exit 1
fi

echo "🚀 Running recipe: $recipe_file"

# Execute COSIMA recipe (could be Python script or Jupyter notebook)
if [[ "$recipe_file" == *.py ]]; then
    python "$recipe_file"
elif [[ "$recipe_file" == *.ipynb ]]; then
    jupyter nbconvert --to notebook --execute "$recipe_file"
else
    echo "ERROR: Unsupported recipe format"
    exit 1
fi

echo "Job completed at: $(date)"
"""
        return pbs_script

    def generate_pbs_script(self, recipe_name: str, config: Dict, 
                           recipe_type: str = 'esmvaltool', 
                           esmvaltool_version: str = 'main', 
                           conda_module: str = 'conda/analysis3',
                           project: str = 'w40',
                           repository_url: str = None) -> str:
        """Generate PBS script based on recipe type."""
        
        if recipe_type.lower() == 'cosima':
            return self.generate_cosima_pbs_script(recipe_name, config, project)
        else:
            # Default to ESMValTool
            return self.generate_esmvaltool_pbs_script(recipe_name, config, esmvaltool_version, 
                                                      conda_module, project)

    def run(self, recipe_name: str, config_json: str = '{}', 
            recipe_type: str = 'esmvaltool',
            esmvaltool_version: str = 'main', 
            conda_module: str = 'conda/analysis3',
            project: str = 'w40',
            repository_url: str = None) -> tuple[str, str]:
        """
        Generate PBS script for HPC execution via ssh-action.
        
        Args:
            recipe_name: Name of the recipe to run
            config_json: JSON configuration string (may include storage directive)
            recipe_type: Type of recipe ('esmvaltool' or 'cosima')
            esmvaltool_version: ESMValTool version (for esmvaltool recipes)
            conda_module: Conda module to load
            project: PBS project code (e.g., w40, kj13, etc.)
            repository_url: Repository URL to clone (optional)
            
        Returns:
            (status, pbs_filename)
        """
        print(f"🎯 Generating {recipe_type.upper()} PBS script for recipe '{recipe_name}'")
        
        # Parse configuration
        config = json.loads(config_json) if config_json else {}
        
        # Set defaults based on recipe type
        if recipe_type.lower() == 'cosima':
            default_config = {
                'queue': 'normal',
                'memory': '8gb', 
                'walltime': '04:00:00',
                'group': 'large'
            }
        else:
            # ESMValTool defaults
            default_config = {
                'queue': 'normal',
                'memory': '4gb', 
                'walltime': '02:00:00',
                'group': 'medium'
            }
        
        config = {**default_config, **config}
        
        print(f"📋 Using configuration:")
        print(f"  Recipe Type: {recipe_type}")
        print(f"  Queue: {config['queue']}")
        print(f"  Memory: {config['memory']}")
        print(f"  Walltime: {config['walltime']}")
        print(f"  Group: {config['group']}")
        print(f"  Project: {project}")
        if config.get('storage'):
            print(f"  Storage: {config['storage']}")
        if repository_url:
            print(f"  Repository: {repository_url}")
        
        # Generate PBS script
        pbs_script = self.generate_pbs_script(
            recipe_name=recipe_name, 
            config=config, 
            recipe_type=recipe_type,
            esmvaltool_version=esmvaltool_version,
            conda_module=conda_module,
            project=project,
            repository_url=repository_url
        )
        
        # Save PBS script for ssh-action to use
        pbs_filename = f"launch_{recipe_name}.pbs"
        with open(pbs_filename, 'w') as f:
            f.write(pbs_script)
        
        print(f"✅ PBS script saved to: {pbs_filename}")
        print("� Ready for upload and submission via ssh-action")
        
        return ('pbs-generated', pbs_filename)
    

def main():
    parser = argparse.ArgumentParser(description='Smart Recipe Runner - HPC PBS Generator')
    parser.add_argument('--recipe', required=True, help='Recipe name')
    parser.add_argument('--config', default='{}', help='Recipe config as JSON')
    parser.add_argument('--recipe-type', default='esmvaltool', 
                       choices=['esmvaltool', 'cosima'], 
                       help='Type of recipe to run')
    parser.add_argument('--esmvaltool-version', default='main', help='ESMValTool version')
    parser.add_argument('--conda-module', default='conda/analysis3', help='Conda module')
    parser.add_argument('--project', default='w40', help='PBS project code (e.g., w40, kj13, etc.)')
    parser.add_argument('--repository-url', help='Repository URL to clone')
    
    args = parser.parse_args()
    
    try:
        runner = SmartRecipeRunner()
        status, pbs_file = runner.run(
            recipe_name=args.recipe,
            config_json=args.config,
            recipe_type=args.recipe_type,
            esmvaltool_version=args.esmvaltool_version,
            conda_module=args.conda_module,
            project=args.project,
            repository_url=args.repository_url
        )
        
        print(f"✅ PBS generation completed with status: {status}")
        print(f"📄 PBS file: {pbs_file}")
        print("🚀 Ready for HPC execution via ssh-action")
            
    except Exception as e:
        print(f"❌ Error in PBS generation: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
