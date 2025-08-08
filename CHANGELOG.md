# Changelog

All notable changes to the Smart Recipe Runner will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# Changelog

All notable changes to the Smart Recipe Runner will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Password-protected SSH key support**: Added `gadi_ssh_passphrase` parameter for secure SSH key authentication
- **Enhanced security**: Support for both standard and password-protected SSH keys for Gadi connections
- **Conditional execution**: SSH-related steps only run when job submission is requested (submit_job=true)
- **Internet-safe PBS architecture**: Repository cloning now happens on login nodes (with internet) before job submission
- **Queue compatibility**: PBS jobs now work on all queues, including those without internet access
- **Enhanced repository management**: Robust cloning and updating of ESMValTool/COSIMA repositories on Gadi login nodes
- **Pre-cloned repository validation**: PBS scripts verify repositories exist before attempting execution
- **Comprehensive recipe search**: Multiple search locations and formats for better recipe discovery
- **Improved error handling**: Lists available recipes when target recipe is not found
- **Better logging**: Detailed status messages during repository setup and recipe search
- **Full Gadi integration restored**: Direct SSH connection and job submission to Gadi HPC using appleboy/ssh-action
- **Dual execution modes**: Generate-only mode and full execution mode with job submission
- **Job monitoring**: Returns job path and status information for submitted jobs
- **Reliable SSH integration**: Uses well-established appleboy/ssh-action for secure connections
- Comprehensive error handling for SSH operations
- Flexible directory configuration for script placement on Gadi
- Base64 encoding for safe PBS script transfer over SSH

### Enhanced
- **Repository cloning strategy**: Moved from PBS job (compute nodes) to SSH action (login nodes) for internet access
- **Repository cloning**: More robust with proper error handling and git fetch before pull
- **Recipe discovery**: Searches multiple directories (main, examples, notebooks, scripts) and file formats
- **Diagnostic output**: Shows available recipes when specified recipe is not found
- **PBS script reliability**: No longer requires internet access during job execution

### Restored
- Complete HPC workflow: Clone repositories → Generate PBS → Upload → Submit → Monitor
- Repository management on target HPC system (now on login nodes)
- Direct qsub integration for job submission
- Job ID tracking and status monitoring

### Technical Improvements
- **Separation of concerns**: Repository management (login nodes) vs computation (compute nodes)
- **Network independence**: PBS jobs can run on any queue regardless of internet restrictions
- **Error resilience**: Better handling of network issues during repository operations

### Features
- **Automatic Resource Detection**: Heuristic analysis of recipes to determine optimal resource allocation
- **Configuration Management**: Self-updating configuration files with change detection
- **Multiple Execution Modes**: Generate-only or full execution with job submission
- **HPC Integration**: Full PBS integration with job submission, monitoring, and cleanup
- **Error Handling**: Comprehensive error reporting and debugging capabilities
- **Security**: Secure credential management through GitHub secrets
- **Repository Integration**: Automatic cloning and updating of recipe repositories on Gadi
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
