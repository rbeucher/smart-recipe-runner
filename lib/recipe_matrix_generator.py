#!/usr/bin/env python3
"""
Recipe List Generator for GitHub Actions Matrix

This script reads a YAML configuration file and outputs a JSON list of enabled recipes
that can be used to generate a GitHub Actions matrix for parallel execution.
"""

import argparse
import json
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Any


def load_config(config_path: str) -> Dict[str, Any]:
    """Load and validate YAML configuration file."""
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML configuration: {e}")
    
    return config


def load_config_from_string(config_content: str) -> Dict[str, Any]:
    """Load and validate YAML configuration from string content."""
    try:
        config = yaml.safe_load(config_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML configuration: {e}")
    
    return config


def get_enabled_recipes(config: Dict[str, Any], selected_recipes: List[str] = None) -> List[Dict[str, Any]]:
    """Get list of enabled recipes from configuration."""
    all_recipes = config.get('recipes', [])
    global_defaults = config.get('defaults', {})
    
    # Filter by selection if provided
    if selected_recipes:
        selected_set = set(selected_recipes)
        filtered_recipes = []
        for recipe in all_recipes:
            if recipe['name'] in selected_set:
                filtered_recipes.append(recipe)
                selected_set.remove(recipe['name'])
        
        # Check if any selected recipes were not found
        if selected_set:
            raise ValueError(f"Selected recipes not found in configuration: {list(selected_set)}")
        
        all_recipes = filtered_recipes
    
    # Filter by enabled status and merge with defaults
    enabled_recipes = []
    for recipe in all_recipes:
        if recipe.get('enabled', True):  # Default to enabled if not specified
            # Merge global defaults with recipe-specific config
            merged_recipe = merge_config(global_defaults, recipe)
            enabled_recipes.append(merged_recipe)
    
    return enabled_recipes


def merge_config(global_defaults: Dict[str, Any], recipe: Dict[str, Any]) -> Dict[str, Any]:
    """Merge global defaults with recipe-specific configuration."""
    merged = {}
    
    # Start with global defaults
    for key, value in global_defaults.items():
        merged[key] = value
    
    # Override with recipe-specific values
    for key, value in recipe.items():
        if key == 'config':
            # Deep merge config dictionaries
            merged_config = merged.get('config', {}).copy()
            merged_config.update(value)
            merged['config'] = merged_config
        else:
            merged[key] = value
    
    return merged


def format_for_matrix(recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Format recipes for GitHub Actions matrix."""
    matrix_recipes = []
    
    for recipe in recipes:
        # Extract all necessary fields for the matrix
        matrix_recipe = {
            'recipe_name': recipe['name'],
            'recipe_type': recipe.get('type', 'esmvaltool'),
            'recipe_config': json.dumps(recipe.get('config', {})),
            'esmvaltool_version': recipe.get('esmvaltool_version', 'main'),
            'conda_module': recipe.get('conda_module', 'conda/analysis3'),
            'project': recipe.get('project', 'w40'),
            'repository_url': recipe.get('repository_url', '')
        }
        matrix_recipes.append(matrix_recipe)
    
    return {'include': matrix_recipes}


def main():
    parser = argparse.ArgumentParser(description='Generate GitHub Actions matrix from recipe configuration')
    parser.add_argument('--config', help='Path to YAML configuration file')
    parser.add_argument('--config-content', help='YAML configuration content as string')
    parser.add_argument('--recipes', help='Comma-separated list of specific recipes to include')
    parser.add_argument('--output', choices=['matrix', 'list', 'count'], default='matrix',
                       help='Output format: matrix (GitHub Actions matrix), list (recipe names), count (number of recipes)')
    
    args = parser.parse_args()
    
    try:
        # Load configuration from file or string content
        if args.config:
            config = load_config(args.config)
        elif args.config_content:
            config = load_config_from_string(args.config_content)
        else:
            raise ValueError("Either --config or --config-content must be provided")
        
        # Parse selected recipes if provided
        selected_recipes = None
        if args.recipes:
            selected_recipes = [r.strip() for r in args.recipes.split(',')]
        
        # Get enabled recipes
        enabled_recipes = get_enabled_recipes(config, selected_recipes)
        
        if args.output == 'matrix':
            # Output GitHub Actions matrix format
            matrix = format_for_matrix(enabled_recipes)
            print(json.dumps(matrix, separators=(',', ':')))
        elif args.output == 'list':
            # Output simple list of recipe names
            recipe_names = [recipe['name'] for recipe in enabled_recipes]
            print(json.dumps(recipe_names))
        elif args.output == 'count':
            # Output count of enabled recipes
            print(len(enabled_recipes))
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
