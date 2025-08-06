# Contributing to Smart Recipe Runner

Thank you for your interest in contributing to the Smart Recipe Runner! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Release Process](#release-process)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Access to a GitHub account
- Basic understanding of GitHub Actions
- Familiarity with ESMValTool (helpful but not required)

### Repository Structure

```
smart-recipe-runner/
├── action.yml                 # Main GitHub Action definition
├── lib/                      # Python modules
│   ├── config-manager.py     # Configuration management
│   ├── recipe-runner.py      # HPC execution logic
│   └── requirements.txt      # Python dependencies
├── docs/                     # Documentation
├── examples/                 # Example workflows
├── tests/                    # Test suite
├── .github/                  # GitHub-specific files
│   ├── workflows/           # CI/CD workflows
│   └── ISSUE_TEMPLATE/      # Issue templates
└── README.md                # Main documentation
```

## Development Setup

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/smart-recipe-runner.git
   cd smart-recipe-runner
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r lib/requirements.txt
   pip install pylint flake8 pytest
   ```

3. **Set up pre-commit hooks** (optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Contributing Process

### 1. Create an Issue

Before starting work, create an issue to discuss:
- Bug reports
- Feature requests
- Documentation improvements
- Questions about the project

### 2. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### 3. Make Changes

- Follow the coding standards (see below)
- Write or update tests as needed
- Update documentation if required
- Ensure all tests pass

### 4. Test Your Changes

```bash
# Run linting
flake8 lib/

# Run tests
python -m pytest tests/ -v

# Test GitHub Action syntax
python -c "import yaml; yaml.safe_load(open('action.yml'))"
```

### 5. Commit Changes

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "Add feature: description of what you added"
```

### 6. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

## Coding Standards

### Python Code

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

Example:
```python
def calculate_complexity_score(recipe_content: dict) -> int:
    """
    Calculate complexity score for a recipe.
    
    Args:
        recipe_content: Parsed recipe YAML content
        
    Returns:
        Complexity score (0-100)
    """
    # Implementation here
    pass
```

### YAML Files

- Use 2-space indentation
- Quote strings when necessary
- Use descriptive names for workflows and jobs
- Include comments for complex configurations

### Documentation

- Use clear, concise language
- Include code examples
- Keep documentation up to date with code changes
- Use proper Markdown formatting

## Testing

### Test Categories

1. **Unit Tests**: Test individual functions and components
2. **Integration Tests**: Test component interactions
3. **Action Tests**: Test the GitHub Action functionality
4. **Documentation Tests**: Validate documentation and examples

### Writing Tests

- Write tests for all new functionality
- Test both success and failure cases
- Use meaningful test names
- Include edge cases
- Mock external dependencies (SSH, file system, etc.)

Example:
```python
def test_classify_recipe_complexity_small():
    """Test classification of small recipes."""
    recipe = {
        'diagnostics': {'simple': {'variables': {'tas': {}}}},
        'datasets': [{'dataset': 'Model1'}]
    }
    
    complexity = config_manager._classify_recipe_complexity(recipe)
    assert complexity == 'small'
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_config_manager.py -v

# Run with coverage
python -m pytest tests/ --cov=lib --cov-report=html
```

## Documentation

### Types of Documentation

1. **Code Documentation**: Docstrings and inline comments
2. **User Documentation**: README, configuration guides
3. **Developer Documentation**: Architecture, contributing guides
4. **Examples**: Working example workflows

### Documentation Standards

- Keep documentation current with code changes
- Use clear examples
- Include troubleshooting information
- Test all example code

### Building Documentation

```bash
# Validate documentation
python -c "
import os
docs = ['README.md', 'docs/architecture.md', 'docs/configuration.md']
for doc in docs:
    if not os.path.exists(doc):
        print(f'Missing: {doc}')
    elif os.path.getsize(doc) == 0:
        print(f'Empty: {doc}')
    else:
        print(f'OK: {doc}')
"
```

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH` (e.g., 1.2.3)
- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes (backward compatible)

### Release Steps

1. **Update CHANGELOG.md**
   - Move unreleased changes to new version section
   - Include all notable changes

2. **Create Release Tag**
   ```bash
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```

3. **GitHub Release**
   - Automated via GitHub Actions
   - Includes changelog and artifacts

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if applicable)
- [ ] Branch is up to date with main

### Pull Request Description

Include:
- **Summary**: What changes are made and why
- **Testing**: How the changes were tested
- **Breaking Changes**: Any breaking changes (if applicable)
- **Related Issues**: Link to related issues

Example:
```markdown
## Summary
Add support for custom resource groups in configuration.

## Changes
- Added custom resource group validation
- Updated configuration schema
- Added tests for new functionality

## Testing
- Unit tests added for new validation logic
- Integration test with custom resource group
- Manual testing with example workflows

## Related Issues
Closes #123
```

### Review Process

- At least one maintainer review required
- All CI checks must pass
- Address all review feedback
- Squash commits if requested

## Getting Help

### Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [ESMValTool Documentation](https://esmvaltool.readthedocs.io/)
- [Python Documentation](https://docs.python.org/)

### Communication

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub discussions for questions and ideas
- **Security**: Report security issues privately via email

### Mentorship

New contributors are welcome! If you're new to:
- GitHub Actions development
- Python programming
- ESMValTool workflows
- Open source contribution

Feel free to ask questions in issues or discussions.

## Recognition

Contributors are recognized in:
- Release notes
- Contributors section of README
- GitHub contributor graph

Thank you for contributing to the Smart Recipe Runner! 🎉
