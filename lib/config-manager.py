#!/usr/bin/env python3
"""
Smart Configuration Manager for ESMValTool Recipe CI/CD

This module handles automatic configuration management, including:
- Detecting when configuration needs updating
- Auto-generating configuration from recipes
- Providing fallback resource detection
- Smart caching to avoid unnecessary regeneration
"""

import argparse
import json
import os
import re
import sys
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import re


@dataclass
class ResourceConfig:
    """Resource configuration for a recipe."""
    queue: str
    memory: str
    walltime: str
    max_parallel_tasks: Optional[int]
    group: str


class SmartConfigManager:
    """Intelligent configuration manager for ESMValTool recipes."""
    
    def __init__(self, recipe_dir: str, config_path: str, hpc_system: str = 'gadi'):
        self.recipe_dir = Path(recipe_dir)
        self.config_path = Path(config_path)
        self.hpc_system = hpc_system
        self.config_cache = {}
        
        # Default resource mappings based on analysis of existing recipes
        self.default_resources = {
            'light': ResourceConfig(
                queue='copyq',
                memory='32GB',
                walltime='2:00:00',
                max_parallel_tasks=None,
                group='light'
            ),
            'medium': ResourceConfig(
                queue='normal',
                memory='64GB', 
                walltime='4:00:00',
                max_parallel_tasks=None,
                group='medium'
            ),
            'heavy': ResourceConfig(
                queue='normal',
                memory='128GB',
                walltime='8:00:00',
                max_parallel_tasks=None,
                group='heavy'
            ),
            'megamem': ResourceConfig(
                queue='megamem',
                memory='1000GB',
                walltime='8:00:00',
                max_parallel_tasks=1,
                group='megamem'
            )
        }
        
        # Known high-resource recipes (from legacy config analysis)
        self.known_heavy_recipes = {
            'recipe_anav13jclim', 'recipe_bock20jgr_fig_6-7', 'recipe_bock20jgr_fig_8-10',
            'recipe_check_obs', 'recipe_collins13ipcc', 'recipe_schlund20esd',
            'recipe_ipccwg1ar6ch3_fig_3_42_a', 'recipe_ipccwg1ar6ch3_fig_3_9'
        }
        
        self.known_megamem_recipes = {
            'recipe_collins13ipcc', 'recipe_schlund20esd', 'recipe_ipccwg1ar6ch3_fig_3_42_a'
        }

    def load_existing_config(self) -> Optional[Dict]:
        """Load existing configuration if it exists."""
        if not self.config_path.exists():
            return None
            
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load existing config: {e}")
            return None

    def get_config_hash(self) -> str:
        """Generate hash of recipe directory to detect changes."""
        hasher = hashlib.md5()
        
        # Include all recipe files in hash
        recipe_files = []
        if self.recipe_dir.exists():
            for recipe_file in self.recipe_dir.rglob('*.yml'):
                recipe_files.append(str(recipe_file))
        
        recipe_files.sort()  # Ensure consistent ordering
        
        for recipe_file in recipe_files:
            hasher.update(recipe_file.encode())
            try:
                with open(recipe_file, 'rb') as f:
                    hasher.update(f.read())
            except Exception:
                pass  # Skip files we can't read
                
        return hasher.hexdigest()

    def should_regenerate_config(self, force: bool = False) -> bool:
        """Determine if configuration should be regenerated."""
        if force:
            return True
            
        # Check if config file exists
        if not self.config_path.exists():
            print("Config file doesn't exist, regenerating...")
            return True
            
        # Load existing config and check metadata
        existing_config = self.load_existing_config()
        if not existing_config:
            print("Could not load existing config, regenerating...")
            return True
            
        # Check if recipe hash has changed
        current_hash = self.get_config_hash()
        stored_hash = existing_config.get('metadata', {}).get('recipe_hash')
        
        if current_hash != stored_hash:
            print(f"Recipe directory changed (hash mismatch), regenerating...")
            return True
            
        print("Configuration is up to date")
        return False

    def analyze_recipe_complexity(self, recipe_path: Path) -> str:
        """Analyze a recipe file to determine its resource requirements."""
        recipe_name = recipe_path.stem
        
        # Check known classifications first
        if recipe_name in self.known_megamem_recipes:
            return 'megamem'
        elif recipe_name in self.known_heavy_recipes:
            return 'heavy'
            
        try:
            with open(recipe_path, 'r') as f:
                content = f.read()
                
            # Parse YAML to analyze structure
            recipe_data = yaml.safe_load(content)
            
            # Heuristics for resource classification
            complexity_score = 0
            
            # Check for multiple datasets
            datasets = recipe_data.get('datasets', [])
            if len(datasets) > 10:
                complexity_score += 2
            elif len(datasets) > 5:
                complexity_score += 1
                
            # Check for multiple diagnostics
            diagnostics = recipe_data.get('diagnostics', {})
            if len(diagnostics) > 3:
                complexity_score += 2
            elif len(diagnostics) > 1:
                complexity_score += 1
                
            # Check for memory-intensive operations
            content_lower = content.lower()
            memory_keywords = ['climwip', 'ipcc', 'cmip6', 'bias', 'multimodel', 'ensemble']
            for keyword in memory_keywords:
                if keyword in content_lower:
                    complexity_score += 1
                    
            # Time-intensive operations
            time_keywords = ['timeseries', 'trend', 'climatology', 'annual', 'seasonal']
            for keyword in time_keywords:
                if keyword in content_lower:
                    complexity_score += 0.5
                    
            # Classify based on score
            if complexity_score >= 4:
                return 'heavy'
            elif complexity_score >= 2:
                return 'medium'
            else:
                return 'light'
                
        except Exception as e:
            print(f"Warning: Could not analyze recipe {recipe_name}: {e}")
            return 'medium'  # Safe default

    def generate_config(self, project: str, storage_paths: str) -> Dict:
        """Generate configuration from recipe analysis."""
        print("Generating configuration from recipe analysis...")
        
        config = {
            'metadata': {
                'generated_by': 'Smart Recipe Runner',
                'recipe_hash': self.get_config_hash(),
                'hpc_system': self.hpc_system,
                'project': project,
                'storage_paths': storage_paths.split(',')
            },
            'recipes': []
        }
        
        recipe_count = {'light': 0, 'medium': 0, 'heavy': 0, 'megamem': 0}
        
        # Process all recipe files
        if self.recipe_dir.exists():
            for recipe_path in self.recipe_dir.rglob('*.yml'):
                try:
                    complexity = self.analyze_recipe_complexity(recipe_path)
                    resource_config = self.default_resources[complexity]
                    
                    recipe_config = {
                        'name': recipe_path.stem,
                        'queue': resource_config.queue,
                        'memory': resource_config.memory,
                        'walltime': resource_config.walltime,
                        'group': resource_config.group
                    }
                    
                    if resource_config.max_parallel_tasks:
                        recipe_config['max_parallel_tasks'] = resource_config.max_parallel_tasks
                        
                    config['recipes'].append(recipe_config)
                    recipe_count[complexity] += 1
                    
                except Exception as e:
                    print(f"Warning: Skipping recipe {recipe_path.stem}: {e}")
                    
        # Add summary statistics
        config['metadata']['summary'] = {
            'total_recipes': sum(recipe_count.values()),
            'resource_groups': recipe_count
        }
        
        print(f"Generated config for {sum(recipe_count.values())} recipes:")
        for group, count in recipe_count.items():
            print(f"  {group}: {count} recipes")
            
        return config

    def save_config(self, config: Dict) -> None:
        """Save configuration to file."""
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
        print(f"Configuration saved to {self.config_path}")

    def get_recipe_config(self, recipe_name: str, config: Dict) -> Optional[Dict]:
        """Get configuration for a specific recipe."""
        for recipe in config.get('recipes', []):
            if recipe['name'] == recipe_name:
                return recipe
        return None

    def get_fallback_config(self, recipe_name: str) -> Dict:
        """Get fallback configuration when no config is available."""
        print(f"Using fallback configuration for {recipe_name}")
        
        # Use heuristics to guess resource requirements
        if recipe_name in self.known_megamem_recipes:
            resource = self.default_resources['megamem']
        elif recipe_name in self.known_heavy_recipes:
            resource = self.default_resources['heavy']
        else:
            resource = self.default_resources['medium']  # Safe default
            
        return {
            'name': recipe_name,
            'queue': resource.queue,
            'memory': resource.memory,
            'walltime': resource.walltime,
            'group': resource.group,
            'max_parallel_tasks': resource.max_parallel_tasks
        }

    def run(self, recipe_name: str, mode: str, force_regen: bool, 
            project: str, storage_paths: str) -> Tuple[str, Dict, str]:
        """
        Main execution logic.
        
        Returns:
            (status, recipe_config, resource_group)
        """
        should_run = True
        config_status = 'existing'
        
        # Handle different modes
        if mode == 'config-check':
            should_run = False
            
        elif mode == 'dry-run':
            should_run = False
            print("Running in dry-run mode - no actual execution")
            
        # Check if we need to regenerate config
        if self.should_regenerate_config(force_regen):
            try:
                config = self.generate_config(project, storage_paths)
                self.save_config(config)
                config_status = 'regenerated'
            except Exception as e:
                print(f"Error generating config: {e}")
                config = None
                config_status = 'error'
        else:
            config = self.load_existing_config()
            
        # Get recipe-specific configuration
        if config:
            recipe_config = self.get_recipe_config(recipe_name, config)
            if not recipe_config:
                print(f"Recipe {recipe_name} not found in config, using fallback")
                recipe_config = self.get_fallback_config(recipe_name)
        else:
            print("No configuration available, using fallback")
            recipe_config = self.get_fallback_config(recipe_name)
            
        resource_group = recipe_config.get('group', 'medium')
        
        # Output results for GitHub Actions
        with open(os.environ.get('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
            f.write(f"status={config_status}\n")
            f.write(f"should_run={str(should_run).lower()}\n")
            f.write(f"resource_group={resource_group}\n")
            f.write(f"recipe_config={json.dumps(recipe_config)}\n")
        
        return config_status, recipe_config, resource_group


    def generate_execution_matrix(self, 
                                  recipe_filter: str = ".*", 
                                  resource_filter: str = "all",
                                  max_parallel: int = 8) -> Dict[str, Any]:
        """
        Generate execution matrix for multiple recipes.
        
        Args:
            recipe_filter: Regex pattern or comma-separated list to filter recipes
            resource_filter: Resource group filter (all, small, medium, large, extra-large)
            max_parallel: Maximum parallel executions
            
        Returns:
            Dictionary containing matrix configuration and metadata
        """
        print(f"🔄 Generating execution matrix...")
        print(f"Recipe filter: {recipe_filter}")
        print(f"Resource filter: {resource_filter}")
        
        # Get all recipes from filesystem
        all_recipes = self._discover_recipes()
        
        # Apply recipe filtering
        filtered_recipes = self._filter_recipes(all_recipes, recipe_filter)
        print(f"📋 Found {len(filtered_recipes)} recipes after filtering")
        
        # Group recipes by resource requirements
        recipe_groups = {}
        total_recipes = 0
        
        for recipe in filtered_recipes:
            group = self._classify_recipe_by_name(recipe)
            
            # Apply resource group filter
            if resource_filter != 'all' and group != resource_filter:
                continue
            
            if group not in recipe_groups:
                recipe_groups[group] = []
            recipe_groups[group].append(recipe)
            total_recipes += 1
        
        # Generate matrix structure for GitHub Actions
        matrix_include = []
        for group, recipes in recipe_groups.items():
            for recipe in recipes:
                matrix_include.append({
                    'recipe': recipe,
                    'group': group
                })
        
        matrix = {
            'include': matrix_include,
            'max-parallel': min(max_parallel, total_recipes)
        }
        
        result = {
            'matrix': json.dumps(matrix),
            'total_recipes': total_recipes,
            'filtered_recipes': json.dumps(filtered_recipes),
            'recipe_groups': recipe_groups
        }
        
        print(f"✅ Generated matrix with {total_recipes} recipes")
        for group, recipes in recipe_groups.items():
            print(f"  {group}: {len(recipes)} recipes")
        
        return result
    
    def _filter_recipes(self, recipes: List[str], filter_pattern: str) -> List[str]:
        """Filter recipes based on pattern."""
        if not filter_pattern or filter_pattern == ".*":
            return recipes
        
        filtered = []
        
        if ',' in filter_pattern:
            # Comma-separated list
            patterns = [p.strip() for p in filter_pattern.split(',')]
            for recipe in recipes:
                if any(re.search(pattern, recipe) for pattern in patterns):
                    filtered.append(recipe)
        else:
            # Single regex pattern
            pattern = re.compile(filter_pattern)
            for recipe in recipes:
                if pattern.search(recipe):
                    filtered.append(recipe)
        
        return filtered
    
    def _discover_recipes(self) -> List[str]:
        """Discover all available recipes from filesystem."""
        recipes = []
        
        if os.path.exists(self.recipe_dir):
            for root, dirs, files in os.walk(self.recipe_dir):
                for file in files:
                    if file.endswith('.yml') and file.startswith('recipe_'):
                        # Remove extension and path
                        recipe_name = os.path.splitext(file)[0]
                        recipes.append(recipe_name)
        
        return list(set(recipes))  # Remove duplicates
    
    def _classify_recipe_by_name(self, recipe_name: str) -> str:
        """Classify recipe by name patterns."""
        # Use existing classification logic or simple heuristics
        if any(pattern in recipe_name.lower() for pattern in ['example', 'test', 'simple']):
            return 'small'
        elif any(pattern in recipe_name.lower() for pattern in ['climate', 'ensemble', 'multi']):
            return 'large'
        elif any(pattern in recipe_name.lower() for pattern in ['machine_learning', 'ml', 'stat']):
            return 'extra-large'
        else:
            return 'medium'


def main():
    parser = argparse.ArgumentParser(description='Smart Configuration Manager')
    parser.add_argument('--recipe', required=True, help='Recipe name or "all" for matrix generation')
    parser.add_argument('--mode', default='run-only', help='Execution mode')
    parser.add_argument('--config-path', required=True, help='Config file path')
    parser.add_argument('--recipe-dir', required=True, help='Recipe directory')
    parser.add_argument('--force-regen', default='false', help='Force regeneration')
    parser.add_argument('--hpc-system', default='gadi', help='HPC system')
    parser.add_argument('--project', default='w40', help='Project name')
    parser.add_argument('--storage', default='', help='Storage paths')
    # Matrix generation arguments
    parser.add_argument('--generate-matrix', action='store_true', help='Generate execution matrix')
    parser.add_argument('--recipe-filter', default='.*', help='Recipe filter pattern')
    parser.add_argument('--resource-filter', default='all', help='Resource group filter')
    parser.add_argument('--max-parallel', type=int, default=8, help='Maximum parallel executions')
    
    args = parser.parse_args()
    
    manager = SmartConfigManager(
        recipe_dir=args.recipe_dir,
        config_path=args.config_path,
        hpc_system=args.hpc_system
    )
    
    force_regen = args.force_regen.lower() == 'true'
    
    try:
        if args.generate_matrix or args.recipe == 'all':
            # Matrix generation mode
            result = manager.generate_execution_matrix(
                recipe_filter=args.recipe_filter,
                resource_filter=args.resource_filter,
                max_parallel=args.max_parallel
            )
            
            # Output for GitHub Actions
            print(f"::set-output name=matrix::{result['matrix']}")
            print(f"::set-output name=total_recipes::{result['total_recipes']}")
            print(f"::set-output name=filtered_recipes::{result['filtered_recipes']}")
            
            print(f"Matrix generation completed successfully")
            print(f"Total recipes: {result['total_recipes']}")
            
        else:
            # Single recipe configuration mode
            status, recipe_config, resource_group = manager.run(
                recipe_name=args.recipe,
                mode=args.mode,
                force_regen=force_regen,
                project=args.project,
                storage_paths=args.storage
            )
            
            # Output for GitHub Actions
            print(f"::set-output name=status::{status}")
            print(f"::set-output name=resource_group::{resource_group}")
            
            print(f"Configuration management completed successfully")
            print(f"Status: {status}")
            print(f"Resource Group: {resource_group}")
        
    except Exception as e:
        print(f"Error in configuration management: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
