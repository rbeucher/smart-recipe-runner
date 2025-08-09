#!/usr/bin/env python3
"""
Job Tracking Database Manager

Manages job submission tracking using GitHub as a database backend.
Supports multiple storage backends: Issues, JSON files, or GitHub Projects.
"""

import json
import requests
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class JobTracker:
    def __init__(self, github_token: str, repo: str, storage_type: str = "json"):
        self.github_token = github_token
        self.repo = repo  # format: "owner/repo"
        self.storage_type = storage_type
        self.base_url = f"https://api.github.com/repos/{repo}"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def track_job_submission(self, job_data: Dict[str, Any]) -> str:
        """Track a new job submission"""
        job_id = job_data.get('job_id', 'unknown')
        tracking_id = f"job-{job_id}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        
        job_record = {
            "tracking_id": tracking_id,
            "job_id": job_id,
            "recipe_name": job_data.get('recipe_name'),
            "recipe_type": job_data.get('recipe_type'),
            "status": "submitted",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "gadi_path": job_data.get('gadi_path'),
            "github_run_id": os.environ.get('GITHUB_RUN_ID'),
            "github_run_url": f"https://github.com/{self.repo}/actions/runs/{os.environ.get('GITHUB_RUN_ID')}",
            "repository_path": job_data.get('repository_path'),
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "output_files": [],
            "metadata": job_data
        }
        
        if self.storage_type == "issue":
            return self._track_via_issue(job_record)
        elif self.storage_type == "json":
            return self._track_via_json(job_record)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def _track_via_issue(self, job_record: Dict[str, Any]) -> str:
        """Track job using GitHub Issues"""
        title = f"🔄 Job: {job_record['recipe_name']} ({job_record['job_id']})"
        
        body = f"""
## Job Details
- **Recipe**: {job_record['recipe_name']}
- **Type**: {job_record['recipe_type']}
- **Job ID**: {job_record['job_id']}
- **Status**: {job_record['status']}
- **Submitted**: {job_record['submitted_at']}
- **GitHub Run**: [#{os.environ.get('GITHUB_RUN_ID')}]({job_record['github_run_url']})

## Paths
- **Gadi Path**: `{job_record['gadi_path']}`
- **Repository**: `{job_record['repository_path']}`

## Tracking
This issue will be automatically updated with job status changes.

<!-- TRACKING_DATA
{json.dumps(job_record, indent=2)}
-->
"""
        
        issue_data = {
            "title": title,
            "body": body,
            "labels": ["job-tracking", f"status-{job_record['status']}", f"type-{job_record['recipe_type']}"]
        }
        
        response = requests.post(f"{self.base_url}/issues", 
                               headers=self.headers, 
                               json=issue_data)
        
        if response.status_code == 201:
            issue = response.json()
            return f"issue-{issue['number']}"
        else:
            raise Exception(f"Failed to create tracking issue: {response.text}")
    
    def _track_via_json(self, job_record: Dict[str, Any]) -> str:
        """Track job using JSON files in repository"""
        # This would require push access to the repository
        # Implementation would create/update JSON files via GitHub API
        tracking_file = f"tracking/{job_record['tracking_id']}.json"
        
        # Get current content (if exists)
        content = json.dumps(job_record, indent=2)
        
        # Create/update file via GitHub API
        file_data = {
            "message": f"Track job submission: {job_record['recipe_name']}",
            "content": content,
            "branch": "tracking"
        }
        
        # This is a simplified version - full implementation would handle
        # file existence, base64 encoding, etc.
        return job_record['tracking_id']
    
    def update_job_status(self, tracking_id: str, status_update: Dict[str, Any]) -> bool:
        """Update job status"""
        if self.storage_type == "issue":
            return self._update_issue_status(tracking_id, status_update)
        elif self.storage_type == "json":
            return self._update_json_status(tracking_id, status_update)
        return False
    
    def _update_issue_status(self, tracking_id: str, status_update: Dict[str, Any]) -> bool:
        """Update job status via GitHub Issue"""
        issue_number = tracking_id.replace("issue-", "")
        
        # Get current issue
        response = requests.get(f"{self.base_url}/issues/{issue_number}", 
                               headers=self.headers)
        
        if response.status_code != 200:
            return False
        
        issue = response.json()
        
        # Extract current tracking data
        body = issue['body']
        if '<!-- TRACKING_DATA' in body:
            start = body.find('<!-- TRACKING_DATA') + len('<!-- TRACKING_DATA\n')
            end = body.find('\n-->')
            try:
                current_data = json.loads(body[start:end])
            except:
                current_data = {}
        else:
            current_data = {}
        
        # Update data
        current_data.update(status_update)
        current_data['last_checked'] = datetime.now(timezone.utc).isoformat()
        
        # Update issue
        new_status = status_update.get('status', current_data.get('status', 'unknown'))
        
        # Update title if status changed
        new_title = f"🔄 Job: {current_data['recipe_name']} ({current_data['job_id']}) - {new_status.upper()}"
        
        # Update labels
        old_labels = [label['name'] for label in issue['labels']]
        new_labels = [label for label in old_labels if not label.startswith('status-')]
        new_labels.append(f"status-{new_status}")
        
        # Create updated body
        updated_body = body.split('<!-- TRACKING_DATA')[0] + f"""<!-- TRACKING_DATA
{json.dumps(current_data, indent=2)}
-->"""
        
        update_data = {
            "title": new_title,
            "body": updated_body,
            "labels": new_labels
        }
        
        response = requests.patch(f"{self.base_url}/issues/{issue_number}",
                                headers=self.headers,
                                json=update_data)
        
        return response.status_code == 200
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all tracked jobs"""
        if self.storage_type == "issue":
            return self._get_jobs_from_issues()
        elif self.storage_type == "json":
            return self._get_jobs_from_json()
        return []
    
    def _get_jobs_from_issues(self) -> List[Dict[str, Any]]:
        """Get all jobs from GitHub Issues"""
        response = requests.get(f"{self.base_url}/issues",
                               headers=self.headers,
                               params={"labels": "job-tracking", "state": "all"})
        
        if response.status_code != 200:
            return []
        
        jobs = []
        for issue in response.json():
            # Extract tracking data from issue body
            body = issue['body']
            if '<!-- TRACKING_DATA' in body:
                start = body.find('<!-- TRACKING_DATA') + len('<!-- TRACKING_DATA\n')
                end = body.find('\n-->')
                try:
                    job_data = json.loads(body[start:end])
                    job_data['issue_number'] = issue['number']
                    job_data['issue_url'] = issue['html_url']
                    jobs.append(job_data)
                except:
                    pass
        
        return jobs

if __name__ == "__main__":
    # Example usage
    tracker = JobTracker(
        github_token=os.environ.get('GITHUB_TOKEN'),
        repo=os.environ.get('GITHUB_REPOSITORY'),
        storage_type="issue"
    )
    
    # Track a job
    job_data = {
        "job_id": "12345.gadi-pbs",
        "recipe_name": "test_recipe.yml",
        "recipe_type": "esmvaltool",
        "gadi_path": "/scratch/w40/user/scripts/test_recipe.pbs",
        "repository_path": "/scratch/w40/user/ESMValTool-ci"
    }
    
    tracking_id = tracker.track_job_submission(job_data)
    print(f"Job tracked with ID: {tracking_id}")
