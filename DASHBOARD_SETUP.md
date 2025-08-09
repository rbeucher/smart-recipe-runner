# Job Dashboard Setup Guide

This guide helps you set up a comprehensive job tracking and dashboard system for your recipe runner.

## 🎯 Overview

The dashboard system provides:
- **Non-blocking job submission** - Jobs run on Gadi without timing out GitHub runners
- **Real-time status tracking** - Automated monitoring of job progress
- **Web dashboard** - Visual interface to monitor all jobs
- **GitHub integration** - Uses GitHub Issues and Pages for tracking and hosting

## 📋 Setup Steps

### 1. Enable GitHub Pages

1. Go to your repository **Settings** > **Pages**
2. Set **Source** to "GitHub Actions"
3. Your dashboard will be available at: `https://[username].github.io/[repository-name]/`

### 2. Update Repository Secrets

Add these secrets to your repository (**Settings** > **Secrets and variables** > **Actions**):

```
GADI_USER=your_gadi_username
GADI_KEY=your_ssh_private_key
GADI_KEY_PASSPHRASE=your_key_passphrase (if needed)
GADI_SCRIPTS_DIR=/scratch/[project]/[user]/recipe-ci
```

### 3. Configure Workflow Permissions

1. Go to **Settings** > **Actions** > **General**
2. Under "Workflow permissions", select:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**

### 4. Enable Issues (for job tracking)

1. Go to **Settings** > **General**
2. Ensure **Issues** are enabled

## 🚀 Usage

### Submit Jobs Without Timeout

Update your workflow to use non-blocking mode:

```yaml
- name: Execute Recipe
  uses: rbeucher/smart-recipe-runner@main
  with:
    wait_for_completion: 'false'  # 👈 This prevents timeout
    submit_job: 'true'
    gadi_username: ${{ secrets.GADI_USER }}
    gadi_ssh_key: ${{ secrets.GADI_KEY }}
```

### Monitor Jobs

1. **Dashboard**: Visit your GitHub Pages URL to see the visual dashboard
2. **Issues**: Check GitHub Issues for detailed job tracking
3. **Automatic Updates**: The dashboard updates every 15 minutes

## 📊 Dashboard Features

### Job Status Overview
- 📊 **Summary Cards**: Total, Running, Queued, Completed, Failed jobs
- 📋 **Job Table**: Detailed view of all jobs with status and actions
- 🔄 **Auto-refresh**: Updates every 5 minutes automatically

### Job Tracking via Issues
- 🏷️ **Labels**: Automatic labeling by status and recipe type
- 📝 **Details**: Complete job metadata and execution details
- 🔗 **Links**: Direct links to GitHub Actions runs and output files

### Status Categories
- 🟡 **Q** - Queued (waiting to start)
- 🟠 **R** - Running (currently executing)
- 🟢 **C** - Completed successfully
- 🔴 **E** - Error/Failed
- ⚫ **completed** - No longer in queue (check output files)

## 🔧 Customization

### Change Update Frequency

Edit `.github/workflows/job-dashboard.yml`:

```yaml
schedule:
  - cron: '*/5 * * * *'  # Every 5 minutes instead of 15
```

### Use Different Storage Backend

In the tracking step, change storage type:

```python
tracker = JobTracker(
    storage_type="json"  # or "issue"
)
```

### Custom Dashboard Styling

Edit the CSS in the dashboard workflow to match your preferences.

## 🛠️ Troubleshooting

### Dashboard Not Updating

1. Check GitHub Actions tab for workflow failures
2. Verify SSH credentials in repository secrets
3. Ensure GitHub Pages is enabled and configured correctly

### Jobs Not Being Tracked

1. Verify `wait_for_completion: 'false'` is set
2. Check repository permissions allow Issues creation
3. Look for tracking errors in GitHub Actions logs

### SSH Connection Issues

1. Test SSH key manually: `ssh -i key gadi.nci.org.au`
2. Verify key format (should be OpenSSH format)
3. Check if passphrase is required and set correctly

## 📈 Advanced Features

### Custom Notifications

Add webhook notifications for job completion:

```yaml
- name: Notify on Completion
  if: matrix.recipe_type == 'important'
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Data Export

Export dashboard data for analysis:

```bash
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo/issues?labels=job-tracking
```

## 🔍 Monitoring Long-Running Jobs

The system is designed specifically for jobs that exceed GitHub's runner timeout limits:

1. **Submit jobs in non-blocking mode** (`wait_for_completion: false`)
2. **Monitor progress via dashboard** (updates every 15 minutes)
3. **Get notifications** when jobs complete or fail
4. **Access output files** directly on Gadi via tracked paths

This allows you to run jobs that take hours or days without worrying about GitHub Actions timeouts!

## 📞 Support

- **Issues**: Report problems via GitHub Issues
- **Documentation**: Check the README for basic usage
- **Community**: Join discussions in GitHub Discussions (if enabled)

---

**Next Steps**: Run your first tracked job and visit your dashboard URL to see it in action! 🎉
