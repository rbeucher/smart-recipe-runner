# Dashboard Integration Guide

The Smart Recipe Runner includes optional dashboard functionality that provides monitoring, status tracking, and visual reporting of your recipe executions.

## Quick Start

Enable dashboard features by adding the `enable_dashboard: true` parameter to your action:

```yaml
- name: Test Recipe with Dashboard
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    mode: 'recipe'
    recipe_name: 'recipe_python.yml'
    enable_dashboard: true  # ← Enable dashboard features
```

## Dashboard Features

### 📊 **Live Web Dashboard**
- **Visual metrics**: Success rates, execution trends, failure analysis
- **Real-time data**: Auto-updating status and performance metrics
- **Historical tracking**: Trends over time with data retention
- **Responsive design**: Works on desktop and mobile devices

### 🔔 **Automated Status Reporting**
- **Status tracking**: Persistent storage of execution history
- **Issue management**: Automatic GitHub issue creation on failures
- **Artifacts**: Downloadable reports and data files
- **Integration**: Seamless workflow integration

### 📈 **Performance Analytics**
- **Execution metrics**: Runtime, resource usage, success rates
- **Trend analysis**: Performance over time
- **Comparative data**: Multiple recipe/notebook performance
- **Resource optimization**: Insights for improving efficiency

## Configuration Options

### Basic Dashboard Options

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `enable_dashboard` | Enable dashboard features | `false` | `true` |
| `dashboard_update` | When to update dashboard data | `auto` | `always`, `never` |
| `create_status_issue` | Create GitHub issues on failure | `false` | `true` |
| `dashboard_retention_days` | Data retention period | `30` | `60` |

### Dashboard Update Modes

- **`auto`**: Update dashboard when workflow completes successfully
- **`always`**: Update dashboard regardless of workflow status
- **`never`**: Don't update dashboard (only generate local data)

## Usage Examples

### 1. Basic Recipe Testing with Dashboard

```yaml
- name: Test Recipe with Monitoring
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    mode: 'recipe'
    recipe_name: 'recipe_python.yml'
    esmvaltool_version: 'main'
    enable_dashboard: true
    create_status_issue: true
```

### 2. Notebook Testing with Dashboard

```yaml
- name: Test Notebooks with Analytics
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    mode: 'notebook'
    repository_url: 'https://github.com/COSIMA/cosima-recipes'
    notebook_categories: 'appetisers,tutorials'
    enable_dashboard: true
    dashboard_update: 'always'
    dashboard_retention_days: 60
```

### 3. Matrix Testing with Dashboard Aggregation

```yaml
strategy:
  matrix:
    recipe: ['recipe_python.yml', 'recipe_ocean.yml']
    
steps:
  - name: Test ${{ matrix.recipe }}
    uses: ACCESS-NRI/smart-recipe-runner@v1
    with:
      recipe_name: ${{ matrix.recipe }}
      enable_dashboard: true
      dashboard_update: 'auto'
```

### 4. Combined Workflow with Full Dashboard

```yaml
- name: Comprehensive Test with Dashboard
  id: test
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    mode: 'both'
    recipe_name: 'recipe_python.yml'
    repository_url: 'https://github.com/COSIMA/cosima-recipes'
    enable_dashboard: true
    dashboard_update: 'always'
    create_status_issue: true
    dashboard_retention_days: 90

- name: Access Dashboard Results
  run: |
    echo "Dashboard URL: ${{ steps.test.outputs.dashboard_url }}"
    echo "Status: ${{ steps.test.outputs.dashboard_status }}"
```

## Outputs

When dashboard is enabled, additional outputs are available:

| Output | Description | Example |
|--------|-------------|---------|
| `dashboard_url` | Live dashboard URL | `https://user.github.io/repo/` |
| `dashboard_status` | Dashboard generation status | `generated`, `failed`, `disabled` |
| `issue_number` | GitHub issue number (if created) | `123` |

## Dashboard Data Structure

The dashboard generates JSON data files with the following structure:

```json
{
  "summary": {
    "total": 25,
    "success": 22,
    "failure": 2,
    "cancelled": 1
  },
  "workflows": {
    "Test Smart Recipe Runner": {
      "total": 15,
      "success": 14,
      "failure": 1
    }
  },
  "recent_runs": [...],
  "weekly_runs": 8,
  "daily_runs": 3,
  "last_updated": "2025-08-07T10:30:00Z"
}
```

## Accessing the Dashboard

### GitHub Pages Dashboard

1. **Enable GitHub Pages** in your repository settings
2. **Run workflow** with `enable_dashboard: true`
3. **Access dashboard** at `https://username.github.io/repository-name/`

### Local Dashboard Data

Dashboard data is stored in:
- `dashboard_data.json` - Current execution data
- `.github/status/latest.json` - Latest status
- `.github/status/report_*.json` - Historical data

## Integration Patterns

### Weekly Dashboard Updates

```yaml
on:
  schedule:
    - cron: '0 6 * * 1'  # Weekly on Monday

jobs:
  weekly-dashboard-update:
    steps:
      - uses: ACCESS-NRI/smart-recipe-runner@v1
        with:
          mode: 'recipe'
          recipe_name: 'weekly_monitoring_recipe.yml'
          enable_dashboard: true
          dashboard_update: 'always'
```

### PR Status Comments

```yaml
- name: Test with Dashboard
  id: test
  uses: ACCESS-NRI/smart-recipe-runner@v1
  with:
    enable_dashboard: true

- name: Comment PR
  if: github.event_name == 'pull_request'
  uses: actions/github-script@v6
  with:
    script: |
      const status = '${{ steps.test.outputs.status }}';
      const dashboardUrl = '${{ steps.test.outputs.dashboard_url }}';
      
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: `## Recipe Test Results\n\n**Status**: ${status}\n${dashboardUrl ? `📊 [Dashboard](${dashboardUrl})` : ''}`
      });
```

### Artifact Collection

```yaml
- name: Upload Dashboard Data
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: dashboard-data
    path: |
      dashboard_data.json
      .github/status/
    retention-days: 30
```

## Troubleshooting

### Dashboard Not Updating

1. **Check GitHub Pages**: Ensure GitHub Pages is enabled
2. **Verify permissions**: Workflow needs `contents: write` and `pages: write`
3. **Review logs**: Check dashboard generation step logs
4. **Manual trigger**: Try `dashboard_update: 'always'`

### Missing Dashboard Data

1. **Check API limits**: GitHub API rate limiting may affect data collection
2. **Verify token**: Ensure `GITHUB_TOKEN` has sufficient permissions
3. **Review retention**: Old data may have been cleaned up

### Performance Issues

1. **Reduce retention**: Lower `dashboard_retention_days`
2. **Optimize updates**: Use `dashboard_update: 'auto'` instead of `'always'`
3. **Batch operations**: Combine multiple tests in single workflow

## Advanced Configuration

### Custom Dashboard Styling

The dashboard HTML can be customized by modifying the generated CSS in the dashboard generation step.

### Data Export

Dashboard data can be exported for external analytics:

```yaml
- name: Export Dashboard Data
  run: |
    # Convert JSON to CSV
    python -c "
    import json, csv
    with open('dashboard_data.json') as f:
        data = json.load(f)
    # Process and export data
    "
```

### Integration with External Tools

Dashboard data can be sent to external monitoring systems:

```yaml
- name: Send to External Monitor
  if: steps.test.outputs.dashboard_status == 'generated'
  run: |
    curl -X POST "https://monitoring.example.com/api/data" \
      -H "Content-Type: application/json" \
      -d @dashboard_data.json
```

## Best Practices

1. **Enable selectively**: Use dashboard for key workflows, not every test
2. **Set appropriate retention**: Balance storage with historical needs
3. **Monitor API usage**: GitHub API has rate limits
4. **Use auto-update**: Let the system decide when to update
5. **Combine with artifacts**: Upload data for offline analysis
6. **Review regularly**: Check dashboard insights for optimization opportunities

## Support

For dashboard-related issues:
- Check the [troubleshooting guide](troubleshooting.md)
- Review [workflow examples](../examples/)
- Open an [issue](https://github.com/rbeucher/smart-recipe-runner/issues) for bugs
- Join [discussions](https://github.com/rbeucher/smart-recipe-runner/discussions) for questions
