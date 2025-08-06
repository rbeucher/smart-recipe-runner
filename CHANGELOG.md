# Changelog

All notable changes to the Smart Recipe Runner will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Smart Recipe Runner
- Unified GitHub Action replacing deploy-recipe-cicd and run-recipe actions
- Intelligent configuration management with automatic resource detection
- Self-healing configuration system
- Multiple execution modes: run-only, setup-and-run, config-check, dry-run
- Comprehensive resource group classification (small, medium, large, extra-large)
- HPC integration with PBS job submission and monitoring
- ESMValTool multi-version support
- Debug mode and comprehensive logging
- Force configuration regeneration option
- Automatic queue selection based on resource requirements
- SSH connection management and validation
- Configuration change detection and reporting

### Features
- **Automatic Resource Detection**: Heuristic analysis of recipes to determine optimal resource allocation
- **Configuration Management**: Self-updating configuration files with change detection
- **Multiple Execution Modes**: Flexible execution options for different use cases
- **HPC Integration**: Full PBS integration with job submission, monitoring, and cleanup
- **Error Handling**: Comprehensive error reporting and debugging capabilities
- **Security**: Secure credential management through GitHub secrets
- **Extensibility**: Easy addition of custom resource groups and classification rules

### Documentation
- Comprehensive README with quick start guide
- Architecture documentation explaining system design
- Configuration guide with detailed parameter reference
- Troubleshooting guide with common issues and solutions
- Example workflows for basic and advanced usage
- Testing examples and validation workflows

### Testing
- Unit tests for configuration management
- Integration tests for recipe execution
- GitHub Actions CI/CD pipeline
- Syntax validation and linting
- Security checks for credential management
- Documentation validation

## [1.0.0] - 2024-01-XX

### Added
- Initial stable release
- All features from unreleased version
- Production-ready GitHub Action
- Complete documentation suite
- Comprehensive testing framework

---

## Release Notes

### Migration from Legacy Actions

If you're migrating from the old deploy-recipe-cicd and run-recipe actions:

**Before:**
```yaml
- uses: ACCESS-NRI/deploy-recipe-cicd@main
  with:
    recipe: ${{ matrix.recipe }}
- uses: ACCESS-NRI/run-recipe@main
  with:
    recipe: ${{ matrix.recipe }}
```

**After:**
```yaml
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: ${{ matrix.recipe }}
    mode: setup-and-run
```

### Breaking Changes

None - this is the initial release.

### Known Issues

- None currently identified

### Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting guide
- Review the configuration documentation
- Use debug mode for detailed logging
