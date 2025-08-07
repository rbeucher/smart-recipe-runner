# Troubleshooting Guide

This guide helps resolve common issues when using the Smart Recipe Runner.

## Quick Diagnostics

### Health Check Commands

Run these commands to quickly diagnose issues:

```yaml
# Test configuration generation
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: recipe_example
    mode: config-check

# Test without execution
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: recipe_example
    mode: dry-run

# Force regeneration
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: recipe_example
    force_config_regeneration: true
    debug_mode: true
```

## Common Issues and Solutions

### 1. SSH Connection Issues

#### Symptoms
```
Error: Failed to establish SSH connection
Error: Permission denied (publickey)
Error: Connection timed out
```

#### Solutions

**Check SSH Key Format**
```yaml
# Ensure your GADI_KEY secret includes the complete SSH private key
GADI_KEY: |
  <your complete SSH private key>
  <including headers and footers>
  <in standard OpenSSH format>
```

**Verify SSH Key Permissions**
```bash
# On your local machine, test the SSH key
ssh -i ~/.ssh/your_key your_username@gadi.nci.org.au
```

**Common SSH Key Issues**
- Key not in OpenSSH format (convert with `ssh-keygen -p -m OpenSSH -f key`)
- Key includes passphrase but `GADI_KEY_PASSPHRASE` not set
- Key not added to authorized_keys on Gadi
- Wrong username in GADI_USER secret

**Password-Protected SSH Keys**

If your SSH key requires a passphrase, you'll see errors like:
```
Error: Load key "...": incorrect passphrase supplied to decrypt private key
Error: Permission denied (publickey)
```

**Solution:**
1. Set the `GADI_KEY_PASSPHRASE` secret with your key passphrase
2. Ensure your CI environment has `expect` available for automated passphrase handling
3. Alternative: Generate a passphrase-free key specifically for CI/CD

```bash
# Generate a new passphrase-free key for CI/CD
ssh-keygen -t rsa -b 4096 -f ~/.ssh/gadi_ci_key -N ""
# Add the public key to your Gadi authorized_keys
cat ~/.ssh/gadi_ci_key.pub >> ~/.ssh/authorized_keys
```

**Debugging Password-Protected Keys:**
Check the workflow logs for these messages:
- `🔐 Detected password-protected SSH key` - Key passphrase detected
- `✅ Successfully added SSH key to agent` - SSH agent setup successful
- `❌ Failed to add key` - SSH agent setup failed
- `⚠️ Warning: Could not setup SSH agent, falling back to local mode` - Fallback to local execution

#### Debugging SSH Issues
```yaml
- name: Debug SSH Connection
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: test_recipe
    mode: dry-run
    debug_mode: true
```

### 2. Recipe Not Found

#### Symptoms
```
Error: Recipe file not found: recipes/recipe_name.yml
Error: Could not locate recipe in repository
```

#### Solutions

**Check Recipe Location**
```bash
# Recipes should be in one of these locations:
recipes/recipe_name.yml
esmvaltool/recipes/recipe_name.yml
```

**Verify Recipe Name**
```yaml
# Use exact filename without .yml extension
recipe: recipe_example  # ✅ Correct
recipe: recipe_example.yml  # ❌ Incorrect
```

**Check Repository Structure**
```bash
find . -name "*.yml" -path "*/recipes/*" | head -10
```

### 3. Configuration Issues

#### Symptoms
```
Error: Invalid configuration file
Error: Configuration generation failed
Error: Resource allocation error
```

#### Solutions

**Force Configuration Regeneration**
```yaml
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: problematic_recipe
    force_config_regeneration: true
```

**Validate Configuration Manually**
```bash
# Check if configuration file exists and is valid
python3 -c "
import yaml
try:
    with open('.github/config/repository-config.yml', 'r') as f:
        config = yaml.safe_load(f)
    print('✅ Configuration is valid YAML')
    print(f'Version: {config.get(\"version\", \"unknown\")}')
    print(f'Recipes: {len(config.get(\"recipes\", []))}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"
```

**Override Resource Allocation**
```yaml
# If automatic detection fails, specify resources manually
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: problematic_recipe
    memory: 8gb
    cpus: 4
    walltime: "03:00:00"
    queue: normal
```

### 4. PBS Job Submission Issues

#### Symptoms
```
Error: PBS job submission failed
Error: Queue limit exceeded
Error: Insufficient resources requested
```

#### Solutions

**Check Queue Limits**
```yaml
# Use appropriate queue for your resources
queue: normal      # Up to 48 CPUs, 192GB RAM
queue: express     # Fast turnaround, limited time
queue: hugemem     # Large memory jobs (>192GB)
```

**Adjust Resource Requests**
```yaml
# Ensure resources are within queue limits
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: memory_intensive_recipe
    memory: 32gb     # Within normal queue limits
    cpus: 8          # Reasonable CPU count
    walltime: "06:00:00"  # Appropriate time limit
```

**Debug PBS Script Generation**
```yaml
# Use dry-run to see generated PBS script
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: test_recipe
    mode: dry-run
    debug_mode: true
```

### 5. ESMValTool Version Issues

#### Symptoms
```
Error: ESMValTool version not found
Error: Module load failed
Error: Command not found: esmvaltool
```

#### Solutions

**Specify Valid Version**
```yaml
# Use known working versions
esmvaltool_version: main        # Latest development
esmvaltool_version: v2.8.0      # Stable release
esmvaltool_version: develop     # Development branch
```

**Check Available Versions**
```bash
# On Gadi, check available modules
module avail esmvaltool
module avail conda/analysis3
```

### 6. Memory and Resource Issues

#### Symptoms
```
Error: Job killed due to memory limit
Error: Walltime exceeded
Error: Queue wait time too long
```

#### Solutions

**Monitor Resource Usage**
```bash
# Check job resource usage (on Gadi)
qstat -f $PBS_JOBID
qstat -u $USER
```

**Optimize Resource Allocation**
```yaml
# Start with conservative estimates and scale up
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: heavy_recipe
    memory: 16gb     # Start here, increase if needed
    cpus: 8          # Match memory allocation
    walltime: "06:00:00"  # Allow extra time
```

**Use Appropriate Resource Groups**
```yaml
# Let the system choose optimal resources
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: unknown_recipe
    mode: setup-and-run  # Enables automatic classification
```

## Advanced Debugging

### Enable Debug Mode

```yaml
- name: Debug Recipe Execution
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: ${{ github.event.inputs.recipe }}
    debug_mode: true
    mode: dry-run
  env:
    ACTIONS_STEP_DEBUG: true  # Enable GitHub Actions debug logging
```

### Capture Full Logs

```yaml
- name: Run with Full Logging
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: problematic_recipe
    debug_mode: true
  id: recipe-run

- name: Upload Logs on Failure
  if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: debug-logs
    path: |
      *.log
      .github/config/
```

### Manual Configuration Inspection

```yaml
- name: Inspect Configuration
  run: |
    echo "=== Repository Configuration ==="
    if [ -f ".github/config/repository-config.yml" ]; then
      cat .github/config/repository-config.yml
    else
      echo "No configuration file found"
    fi
    
    echo "=== Recipe Files ==="
    find . -name "*.yml" -path "*/recipes/*" | head -20
    
    echo "=== Action Inputs ==="
    echo "Recipe: ${{ inputs.recipe }}"
    echo "Mode: ${{ inputs.mode }}"
    echo "ESMValTool Version: ${{ inputs.esmvaltool_version }}"
```

## Error Code Reference

### Action Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 1 | Recipe not found | Check recipe name and location |
| 2 | SSH connection failed | Verify SSH keys and credentials |
| 3 | Configuration error | Check YAML syntax and regenerate config |
| 4 | PBS submission failed | Check resource limits and queue availability |
| 5 | ESMValTool execution failed | Check recipe syntax and data availability |
| 10 | Invalid input parameters | Verify action inputs |
| 20 | Resource allocation error | Adjust resource requirements |
| 30 | Network/connectivity error | Check HPC system status |

### PBS Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 126 | Permission denied | Check file permissions and SSH keys |
| 127 | Command not found | Verify ESMValTool module and version |
| 137 | Process killed (memory) | Increase memory allocation |
| 143 | Process terminated | Check walltime limits |

## Performance Issues

### Slow Job Submission

```yaml
# Use express queue for quick jobs
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: quick_diagnostic
    queue: express
    walltime: "01:00:00"
```

### Long Queue Wait Times

```yaml
# Use different queue or adjust timing
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: flexible_recipe
    queue: normal
    # Consider running during off-peak hours
```

### Memory Optimization

```yaml
# Start with smaller resources and scale up
- uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: memory_test
    memory: 4gb      # Conservative start
    cpus: 2
    walltime: "02:00:00"
```

## Getting Help

### Information to Include

When reporting issues, include:

1. **Recipe name and content**
2. **Action configuration** (inputs used)
3. **Error messages** (full logs)
4. **Expected vs actual behavior**
5. **GitHub workflow file** (relevant sections)

### Debug Information Commands

```yaml
- name: Collect Debug Info
  if: failure()
  run: |
    echo "=== System Information ==="
    uname -a
    
    echo "=== Repository Structure ==="
    find . -type f -name "*.yml" | head -20
    
    echo "=== Configuration Status ==="
    ls -la .github/config/ || echo "No config directory"
    
    echo "=== Recent Actions ==="
    echo "Recipe: ${{ inputs.recipe }}"
    echo "Mode: ${{ inputs.mode }}"
    echo "Debug: ${{ inputs.debug_mode }}"
```

### Testing Minimal Example

```yaml
name: Minimal Test
on: workflow_dispatch

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Test Basic Functionality
        uses: ACCESS-NRI/smart-recipe-runner@v1
        with:
          recipe: recipe_example
          mode: config-check
          debug_mode: true
```

## Prevention Strategies

### 1. Use Version Pinning
```yaml
uses: ACCESS-NRI/smart-recipe-runner@v1.2.3  # Pin to specific version
```

### 2. Implement Validation Workflows
```yaml
# Test configuration changes before merging
name: Validate Configuration
on:
  pull_request:
    paths:
      - '.github/config/**'
      - 'recipes/**'
```

### 3. Monitor Resource Usage
```yaml
# Regular resource usage reports
- name: Resource Usage Report
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: monitoring_recipe
    mode: config-check
```

### 4. Keep Configurations Updated
```yaml
# Periodic configuration updates
- name: Update Configuration
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    recipe: representative_recipe
    force_config_regeneration: true
    mode: config-check
```

By following this troubleshooting guide, you should be able to resolve most common issues with the Smart Recipe Runner. For complex problems, use the debug mode and error codes to gather detailed information for further analysis.
